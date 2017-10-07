from typing import List, Generic, TypeVar, Dict, Any, Optional
from abc import abstractmethod
from configparser import SectionProxy
import aiohttp
import async_timeout
from . import re

from .data import VerseRange, Passage, SearchResults, Bible


RT = TypeVar('RT')
whitespace_re = re.compile(re.one_or_more(re.WHITESPACE))
number_re = re.compile(re.capture(r'\*\*', re.one_or_more(re.DIGIT), re.DOT, r'\*\*'))


class Service(Generic[RT]):
    config: Optional[SectionProxy]

    def __init__(self, config: Optional[SectionProxy]) -> None:
        self.config = config

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        url = self._get_passage_url(bible['service_version'], verses)
        response = await self.get(url)
        text = self._get_passage_text(response)
        text = whitespace_re.sub(' ', text.strip())

        if bible['rtl']:
            # wrap in [RTL embedding]text[Pop directional formatting]
            text = number_re.sub('\u202b\\1\u202c', text)

        return Passage(text, verses, bible['abbr'])

    async def search(self, bible: Bible, terms: List[str]) -> SearchResults:
        url = self._get_search_url(bible['service_version'], terms)
        response = await self.get(url)
        return self._get_search_results(response)

    @abstractmethod
    def _get_passage_url(self, version: str, verses: VerseRange) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_passage_text(self, response: RT) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_search_url(self, version: str, terms: List[str]) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_search_results(self, response: RT) -> SearchResults:
        raise NotImplementedError

    @abstractmethod
    async def _process_response(self, response: aiohttp.ClientResponse) -> RT:
        raise NotImplementedError

    async def get(self, url: str, **session_options) -> RT:
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return await self._process_response(response)

    async def post(self, url: str, data: Dict[str, Any] = None, **session_options) -> RT:
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                async with session.post(url, data=data) as response:
                    return await self._process_response(response)
