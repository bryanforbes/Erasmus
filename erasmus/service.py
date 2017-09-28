from typing import List, Generic, TypeVar, Dict, Any
from abc import abstractmethod
import aiohttp
import async_timeout
import re

from .json import JSONObject
from .data import VerseRange, Passage, SearchResults


RT = TypeVar('RT')
whitespace_re = re.compile(r'\s+')


class Service(Generic[RT]):
    config: JSONObject

    def __init__(self, config: JSONObject) -> None:
        self.config = config

    async def get_passage(self, version: str, verses: VerseRange) -> Passage:
        url = self._get_passage_url(version, verses)
        response = await self.get(url)
        text = self._get_passage_text(response)
        text = whitespace_re.sub(' ', text.strip())

        return Passage(text, verses)

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        url = self._get_search_url(version, terms)
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
