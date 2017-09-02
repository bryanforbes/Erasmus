from typing import List, Generic, TypeVar
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

    def __init__(self, book: str, chapter: int, verse_start: int, verse_end: int = -1) -> None:
        self.book = book
        self.chapter = chapter
        self.verse_start = verse_start
        self.verse_end = verse_end

    def __str__(self) -> str:
        passage = f'{self.book} {self.chapter}:{self.verse_start}'

        if self.verse_end > 0:
            passage = f'{passage}-{self.verse_end}'

        return passage

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is Passage:
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @classmethod
    def from_string(cls, verse: str) -> 'Passage':
        match = search_reference_re.match(verse)

        if match is None:
            return None

        verse_end = match.group('verse_end')
        if verse_end is None:
            verse_end_int = -1
        else:
            verse_end_int = int(verse_end)

        return cls(
            match.group('book'),
            int(match.group('chapter')),
            int(match.group('verse_start')),
            verse_end_int
        )


class SearchResults(object):
    __slots__ = ('verses', 'total')

    verses: List[Passage]
    total: int

    def __init__(self, verses: List[Passage], total: int) -> None:
        self.verses = verses
        self.total = total

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is SearchResults:
            return self.total == other.total and self.verses == other.verses
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


RT = TypeVar('RT')


class Service(Generic[RT]):
    config: ConfigObject

    def __init__(self, config: ConfigObject) -> None:
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

    async def _process_response(self, response) -> RT:
        raise NotImplementedError

    async def _get(self, url: str, **session_options) -> RT:
        async with aiohttp.ClientSession(**session_options) as session:
            with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return await self._process_response(response)
