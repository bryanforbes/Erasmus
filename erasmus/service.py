from typing import List, Generic, TypeVar, AsyncContextManager
import aiohttp
import async_timeout

from .config import ConfigObject
from .data import Passage, SearchResults


RT = TypeVar('RT')


class Service(Generic[RT]):
    config: ConfigObject

    def __init__(self, config: ConfigObject) -> None:
        self.config = config

    async def get_passage(self, version: str, passage: Passage) -> str:
        url = self._get_passage_url(version, passage)
        response = await self.get(url)
        return self._get_passage_text(response)

    def _get_passage_url(self, version: str, passage: Passage) -> str:
        raise NotImplementedError

    def _get_passage_text(self, response: RT) -> str:
        raise NotImplementedError

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        url = self._get_search_url(version, terms)
        response = await self.get(url)
        return self._get_search_results(response)

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        raise NotImplementedError

    def _get_search_results(self, response: RT) -> SearchResults:
        raise NotImplementedError

    async def get(self, url: str) -> RT:
        raise NotImplementedError

    async def _get(self, url: str, **session_options) -> AsyncContextManager[aiohttp.ClientResponse]:
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                return session.get(url)
