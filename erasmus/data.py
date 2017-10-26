from typing import Optional, List, Dict, TYPE_CHECKING  # noqa
from pathlib import Path
from itertools import chain
from mypy_extensions import TypedDict
from .json import load
from .exceptions import BookNotUnderstoodError, ReferenceNotUnderstoodError
from . import re

if TYPE_CHECKING:  # pragma: no cover
    from .context import Context  # noqa

with (Path(__file__).resolve().parent / 'data' / 'books.json').open() as f:
    books_data = load(f)

# Inspired by https://github.com/TehShrike/verse-reference-regex/blob/master/create-regex.js
_book_re = re.compile(
    re.named_group('book')(re.either(
        *re.escape_all(
            chain.from_iterable([[book.name, book.osis] + book.alt for book in books_data])
        )
    )),
    re.optional(re.DOT)
)

_chapter_start_group = re.named_group('chapter_start')
_chapter_end_group = re.named_group('chapter_end')
_verse_start_group = re.named_group('verse_start')
_verse_end_group = re.named_group('verse_end')
_one_or_more_digit = re.one_or_more(re.DIGIT)
_colon = re.combine(re.any_number_of(re.WHITESPACE), ':', re.any_number_of(re.WHITESPACE))

_search_reference_re = re.compile(
    re.START,
    _book_re,
    re.one_or_more(re.WHITESPACE),
    _chapter_start_group(_one_or_more_digit),
    _colon,
    _verse_start_group(_one_or_more_digit),
    re.optional(re.group(
        re.any_number_of(re.WHITESPACE), '[', re.DASH, '\u2013', '\u2014', ']', re.any_number_of(re.WHITESPACE),
        re.optional(re.group(
            _chapter_end_group(_one_or_more_digit), _colon
        )),
        _verse_end_group(_one_or_more_digit)
    )),
    re.END,
    flags=re.IGNORECASE
)


book_input_map = {}  # type: Dict[str, str]
book_mask_map = {}  # type: Dict[str, int]
for book in books_data:
    for input_string in [book.name, book.osis] + book.alt:  # type: str
        book_input_map[input_string.lower()] = book.name
        book_mask_map[input_string.lower()] = book.section


class Bible(TypedDict):
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool
    books: int


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
    __slots__ = ('book', 'book_mask', 'start', 'end')

    book: str
    book_mask: int
    start: Verse
    end: Optional[Verse]

    def __init__(self, book: str, start: Verse, end: Verse = None) -> None:
        self.book = book_input_map.get(book.lower(), None)
        self.book_mask = book_mask_map.get(book.lower(), None)

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
        match = _search_reference_re.match(verse)

        if match is None:
            raise ReferenceNotUnderstoodError(verse)

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

    @classmethod
    async def convert(cls, ctx: 'Context', argument: str) -> 'VerseRange':
        return cls.from_string(argument)


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
            return self.text == other.text and self.range == other.range and self.version == other.version
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
