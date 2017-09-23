from typing import Optional, List, Dict  # noqa
from pathlib import Path
from .json import load
from .exceptions import BookNotUnderstoodError
import re

search_reference_re = re.compile(
    r'^(?P<book>.*)\.? (?P<chapter_start>\d+):(?P<verse_start>\d+)'
    r'(?:-(?:(?P<chapter_end>\d+):)?(?P<verse_end>\d+))?$'
)

with (Path(__file__).resolve().parent / 'data' / 'books.json').open() as f:
    books_data = load(f)

book_input_map = {}  # type: Dict[str, str]
for book in books_data:
    for input_string in [book.name, book.osis] + book.alt:  # type: str
        book_input_map[input_string.lower()] = book.name


class Verse(object):
    __slots__ = ('chapter', 'verse')

    chapter: int
    verse: int

    def __init__(self, chapter: int, verse: int) -> None:
        self.chapter = chapter
        self.verse = verse

    def __str__(self) -> str:
        return f'{self.chapter}:{self.verse}'

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is Verse:
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class VerseRange(object):
    __slots__ = ('book', 'start', 'end')

    book: str
    start: Verse
    end: Optional[Verse]

    def __init__(self, book: str, start: Verse, end: Verse = None) -> None:
        self.book = book_input_map.get(book.lower(), None)

        if self.book is None:
            raise BookNotUnderstoodError(book)

        self.start = start
        self.end = end

    @property
    def verses(self) -> str:
        verse = str(self.start)

        if self.end is not None:
            if self.end.chapter == self.start.chapter:
                verse += f'-{self.end.verse}'
            else:
                verse += f'-{self.end}'

        return verse

    def __str__(self) -> str:
        return f'{self.book} {self.verses}'

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is VerseRange:
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @classmethod
    def from_string(cls, verse: str) -> 'VerseRange':
        match = search_reference_re.match(verse)

        if match is None:
            return None

        chapter_start_int = int(match.group('chapter_start'))
        start = Verse(chapter_start_int, int(match.group('verse_start')))

        end = None  # type: Optional[Verse]
        end_str = match.group('verse_end')

        if end_str is not None:
            end_int = int(end_str)
            chapter_end_int = chapter_start_int

            chapter_end_str = match.group('chapter_end')
            if chapter_end_str is not None:
                chapter_end_int = int(chapter_end_str)

            end = Verse(chapter_end_int, end_int)

        return cls(match.group('book'), start, end)


truncation_warning = 'The passage was too long and has been truncated:\n\n'
truncation_warning_len = len(truncation_warning) + 3


class Passage(object):
    __slots__ = ('text', 'range', 'version')

    text: str
    range: VerseRange
    version: Optional[str]

    def __init__(self, text: str, range: VerseRange, version: str = None) -> None:
        self.text = text
        self.range = range
        self.version = version

    @property
    def citation(self):
        if self.version is not None:
            return f'{self.range} ({self.version})'
        else:
            return str(self.range)

    def get_truncated(self, limit: int) -> str:
        citation = self.citation
        end = limit - (len(citation) + truncation_warning_len)
        text = self.text[:end]
        return f'{truncation_warning}{text}\u2026\n\n{citation}'

    def __str__(self) -> str:
        return f'{self.text}\n\n{self.citation}'

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is Passage:
            return self.range == other.range and self.version == other.version
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class SearchResults(object):
    __slots__ = ('verses', 'total')

    verses: List[VerseRange]
    total: int

    def __init__(self, verses: List[VerseRange], total: int) -> None:
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
