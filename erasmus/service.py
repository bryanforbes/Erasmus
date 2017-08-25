import aiohttp
import async_timeout

from .config import ConfigObject

class Passage(object):
    __slots__ = ('book', 'chapter', 'verse_start', 'verse_end')

    book: str
    chapter: int
    verse_start: int
    verse_end: int

    def __init__(self, book: str, chapter: int, verse_start: int, verse_end: int = -1):
        self.book = book
        self.chapter = chapter
        self.verse_start = verse_start
        self.verse_end = verse_end

class Service:
    config: ConfigObject

    def __init__(self, config: ConfigObject):
        self.config = config

    async def get_passage(self, version: str, passage: Passage) -> str:
        query = self._parse_passage(passage)
        return await self._get_passage(version, query)

    async def _get_passage(self, version: str, passage: str) -> str:
        raise NotImplementedError

    def _parse_passage(self, passage: Passage) -> str:
        raise NotImplementedError

    async def _process_response(self, response):
        raise NotImplementedError

    async def _get_url(self, url: str, **session_options):
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return await self._process_response(response)
