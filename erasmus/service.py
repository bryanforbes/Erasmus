from typing import List, Generic, TypeVar
from abc import abstractmethod
import aiohttp
import async_timeout

from .config import ConfigObject
from .data import Passage, SearchResults


RT = TypeVar('RT')


def service_call(get_url, transform_response):
    def decorator(func):
        async def operation(self, *args, **kwargs):
            url = getattr(self, get_url)(*args, **kwargs)
            response = await self.get(url)
            return getattr(self, transform_response)(response)

        return operation
    return decorator


class Service(Generic[RT]):
    config: ConfigObject

    def __init__(self, config: ConfigObject) -> None:
        self.config = config

    @service_call('_get_passage_url', '_get_passage_text')
    async def get_passage(self, version: str, passage: Passage) -> str:
        pass

    @service_call('_get_search_url', '_get_search_results')
    async def search(self, version: str, terms: List[str]) -> SearchResults:
        pass

    @abstractmethod
    def _get_passage_url(self, version: str, passage: Passage) -> str:
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
