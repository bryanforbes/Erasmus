from __future__ import annotations

import asyncio
import logging
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, AsyncIterator, Dict, List, Optional

import aiohttp
import async_timeout
from attr import dataclass
from botus_receptus import re
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import ServiceLookupTimeout, ServiceSearchTimeout
from ..protocols import Bible

log = logging.getLogger(__name__)

whitespace_re = re.compile(re.one_or_more(re.WHITESPACE))
bold_re = re.compile(r'__BOLD__')
italic_re = re.compile(r'__ITALIC__')
specials_re = re.compile(re.capture(r'[\*`]'))
number_re = re.compile(re.capture(r'\*\*', re.one_or_more(re.DIGIT), re.DOT, r'\*\*'))


@dataclass(slots=True)
class BaseService(object):
    session: aiohttp.ClientSession
    config: Optional[Dict[str, Any]]

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        log.debug(f'Getting passage {verses} ({bible.abbr})')

        try:
            async with self._request_passage(bible, verses) as passage:
                log.debug(f'Got passage {passage.citation}')
                return passage
        except asyncio.TimeoutError:
            raise ServiceLookupTimeout(bible, verses)

    async def search(
        self, bible: Bible, terms: List[str], *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        try:
            async with self._request_search(
                bible, terms, limit=limit, offset=offset
            ) as response:
                return response
        except asyncio.TimeoutError:
            raise ServiceSearchTimeout(bible, terms)

    @abstractmethod
    def _request_passage(
        self, bible: Bible, verses: VerseRange
    ) -> AsyncContextManager[Passage]:
        raise NotImplementedError

    @abstractmethod
    def _request_search(
        self, bible: Bible, terms: List[str], *, limit: int, offset: int
    ) -> AsyncContextManager[SearchResults]:
        raise NotImplementedError

    def _replace_special_escapes(self, bible: Bible, text: str) -> str:
        text = whitespace_re.sub(' ', text.strip())
        text = specials_re.sub(r'\\\1', text)
        text = bold_re.sub('**', text)
        text = italic_re.sub('_', text)

        if bible.rtl:
            # wrap in [RTL embedding]text[Pop directional formatting]
            text = number_re.sub('\u202b\\1\u202c', text)

        return text

    @asynccontextmanager
    async def get(
        self, url: URL, **request_options: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        log.debug('GET %s', url)
        with async_timeout.timeout(10):
            async with self.session.get(url, **request_options) as response:
                log.debug('Finished GET %s', url)
                yield response

    @asynccontextmanager
    async def post(
        self, url: URL, data: Optional[Dict[str, Any]] = None, **request_options: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        log.debug('POST %s', url)
        with async_timeout.timeout(10):
            async with self.session.post(url, data=data, **request_options) as response:
                log.debug('Finished POST %s', url)
                yield response
