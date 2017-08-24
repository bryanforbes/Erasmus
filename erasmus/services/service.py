import asyncio
import aiohttp
import async_timeout

from ..config import ConfigObject

class Service:
    config: ConfigObject

    def __init__(self, config: ConfigObject):
        self.config = config

    async def get_verse(self, version: str, book: str, chapter: int, verse_min: int, verse_max: int = -1) -> str:
        raise NotImplementedError

    async def _process_response(self, response):
        raise NotImplementedError

    async def _get_url(self, url: str, **session_options):
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return await self._process_response(response)
