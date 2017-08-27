from typing import List
import aiohttp
import async_timeout
import re

from .config import ConfigObject

search_reference_re = re.compile(r'^(?P<book>.*) (?P<chapter>\d+):(?P<verse_start>\d+)(?:-(?P<verse_end>\d+))?$')

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

    def __str__(self):
        passage = f'{self.book} {self.chapter}:{self.verse_start}'

        if self.verse_end > 0:
            passage = f'{passage}-{self.verse_end}'

        return passage

    @staticmethod
    def from_string(verse: str):
        match = search_reference_re.match(verse)

        if match is None:
            return None

        verse_end = match.group('verse_end')
        if verse_end is None:
            verse_end = -1
        else:
            verse_end = int(verse_end)

        return Passage(
            match.group('book'),
            int(match.group('chapter')),
            int(match.group('verse_start')),
            verse_end
        )

class SearchResults(object):
    __slots__ = ('verses', 'total')

    verses: List[Passage]
    total: int

    def __init__(self, verses: List[Passage], total: int):
        self.verses = verses
        self.total = total

class Service:
    config: ConfigObject

    def __init__(self, config: ConfigObject):
        self.config = config

    async def get_passage(self, version: str, passage: Passage) -> str:
        query = self._parse_passage(passage)
        return await self._get_passage(version, query)

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        raise NotImplementedError

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
