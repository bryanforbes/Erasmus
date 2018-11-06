from typing import List, Generic, TypeVar, Dict, Any, Optional
from abc import abstractmethod
from configparser import SectionProxy
from botus_receptus import re
import asyncio
import aiohttp
import async_timeout
import logging
from .exceptions import ServiceLookupTimeout, ServiceSearchTimeout
from yarl import URL

from .data import VerseRange, Passage, SearchResults, Bible


RT = TypeVar('RT')
whitespace_re = re.compile(re.one_or_more(re.WHITESPACE))
bold_re = re.compile(r'__BOLD__')
italic_re = re.compile(r'__ITALIC__')
specials_re = re.compile(re.capture(r'[\*`]'))
number_re = re.compile(re.capture(r'\*\*', re.one_or_more(re.DIGIT), re.DOT, r'\*\*'))

log = logging.getLogger(__name__)


class Service(Generic[RT]):
    config: Optional[SectionProxy]
    session: aiohttp.ClientSession

    def __init__(
        self, config: Optional[SectionProxy], session: aiohttp.ClientSession
    ) -> None:
        self.config = config
        self.session = session

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        url = self._get_passage_url(bible['service_version'], verses)
        log.debug('Getting passage %s', verses)

        try:
            response = await self.get(url)
        except asyncio.TimeoutError:
            raise ServiceLookupTimeout(bible, verses)

        log.debug('Got passage %s', verses)
        text = self._get_passage_text(response)
        text = whitespace_re.sub(' ', text.strip())
        text = specials_re.sub(r'\\\1', text)
        text = bold_re.sub('**', text)
        text = italic_re.sub('_', text)

        if bible['rtl']:
            # wrap in [RTL embedding]text[Pop directional formatting]
            text = number_re.sub('\u202b\\1\u202c', text)

        return Passage(text, verses, bible['abbr'])

    async def search(self, bible: Bible, terms: List[str]) -> SearchResults:
        url = self._get_search_url(bible['service_version'], terms)

        try:
            response = await self.get(url)
        except asyncio.TimeoutError:
            raise ServiceSearchTimeout(bible, terms)

        return self._get_search_results(response)

    @abstractmethod
    def _get_passage_url(self, version: str, verses: VerseRange) -> URL:
        raise NotImplementedError

    @abstractmethod
    def _get_passage_text(self, response: RT) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_search_url(self, version: str, terms: List[str]) -> URL:
        raise NotImplementedError

    @abstractmethod
    def _get_search_results(self, response: RT) -> SearchResults:
        raise NotImplementedError

    @abstractmethod
    async def _process_response(self, response: aiohttp.ClientResponse) -> RT:
        raise NotImplementedError

    async def get(self, url: URL, **request_options: Any) -> RT:
        log.debug('GET %s', url)
        with async_timeout.timeout(10):
            async with self.session.get(url, **request_options) as response:
                log.debug('Finished GET %s', url)
                return await self._process_response(response)

    async def post(
        self, url: URL, data: Optional[Dict[str, Any]] = None, **request_options: Any
    ) -> RT:
        log.debug('POST %s', url)
        with async_timeout.timeout(10):
            async with self.session.post(url, data=data, **request_options) as response:
                log.debug('Finished POST %s', url)
                return await self._process_response(response)
