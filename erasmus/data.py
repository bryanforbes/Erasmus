from __future__ import annotations

from itertools import chain
from pathlib import Path
from re import Match, Pattern
from typing import TYPE_CHECKING, Dict, Final, List, Optional, TypedDict, Union

from attr import attrib, dataclass
from botus_receptus import re
from more_itertools import unique_everseen

from .exceptions import BookNotUnderstoodError, ReferenceNotUnderstoodError
from .json import load

if TYPE_CHECKING:
    from .context import Context


class BookDict(TypedDict):
    name: str
    osis: str
    alt: List[str]
    section: int


with (Path(__file__).resolve().parent / 'data' / 'books.json').open() as f:
    _books_data: Final[List[BookDict]] = load(f)

# Inspired by
# https://github.com/TehShrike/verse-reference-regex/blob/master/create-regex.js
_book_re: Final = re.compile(
    re.named_group('book')(
        re.either(
            *re.escape_all(
                unique_everseen(
                    chain.from_iterable(
                        [
                            [book['name'], book['osis']] + book['alt']
                            for book in _books_data
                        ]
                    )
                )
            )
        )
    ),
    re.optional(re.DOT),
)

_chapter_start_group: Final = re.named_group('chapter_start')
_chapter_end_group: Final = re.named_group('chapter_end')
_verse_start_group: Final = re.named_group('verse_start')
_verse_end_group: Final = re.named_group('verse_end')
_version_group: Final = re.named_group('version')
_one_or_more_digit: Final = re.one_or_more(re.DIGIT)
_colon: Final = re.combine(
    re.any_number_of(re.WHITESPACE), ':', re.any_number_of(re.WHITESPACE)
)

_reference_re: Final = re.compile(
    _book_re,
    re.one_or_more(re.WHITESPACE),
    _chapter_start_group(_one_or_more_digit),
    _colon,
    _verse_start_group(_one_or_more_digit),
    re.optional(
        re.group(
            re.any_number_of(re.WHITESPACE),
            '[',
            re.DASH,
            '\u2013',
            '\u2014',
            ']',
            re.any_number_of(re.WHITESPACE),
            re.optional(re.group(_chapter_end_group(_one_or_more_digit), _colon)),
            _verse_end_group(_one_or_more_digit),
        )
    ),
    flags=re.IGNORECASE,
)

_reference_with_version_re: Final = re.compile(
    _reference_re,
    re.optional(
        re.group(
            re.any_number_of(re.WHITESPACE),
            _version_group(re.one_or_more(re.ALPHANUMERICS)),
        )
    ),
    flags=re.IGNORECASE,
)

_reference_or_bracketed_with_version_re: Final = re.compile(
    re.optional(
        re.named_group('bracket')(re.LEFT_BRACKET, re.any_number_of(re.WHITESPACE))
    ),
    _reference_re,
    '(?(bracket)',
    re.group(
        re.optional(
            re.group(
                re.one_or_more(re.WHITESPACE),
                _version_group(re.one_or_more(re.ALPHANUMERICS)),
            )
        ),
        re.any_number_of(re.WHITESPACE),
        re.RIGHT_BRACKET,
    ),
    '|)',
    flags=re.IGNORECASE,
)

_bracketed_reference_with_version_re: Final = re.compile(
    re.LEFT_BRACKET,
    re.any_number_of(re.WHITESPACE),
    _reference_with_version_re,
    re.any_number_of(re.WHITESPACE),
    re.RIGHT_BRACKET,
    flags=re.IGNORECASE,
)

_search_reference_re: Final = re.compile(
    re.START, _reference_re, re.END, flags=re.IGNORECASE
)

_book_input_map: Final[Dict[str, str]] = {}
_book_mask_map: Final[Dict[str, int]] = {}

for _book in _books_data:
    for input_string in [_book['name'], _book['osis']] + _book['alt']:  # type: str
        _book_input_map[input_string.lower()] = _book['name']
    _book_mask_map[_book['name']] = _book['section']


def get_book(book_name_or_abbr: str) -> str:
    book = _book_input_map.get(book_name_or_abbr.lower(), '')

    if book == '':
        raise BookNotUnderstoodError(book)

    return book


def get_book_mask(book_name: str) -> int:
    return _book_mask_map.get(book_name, 0)


@dataclass(slots=True)
class Verse(object):
    chapter: int
    verse: int

    def __str__(self) -> str:
        return f'{self.chapter}:{self.verse}'


@dataclass(slots=True)
class VerseRange(object):
    book: str
    start: Verse
    end: Optional[Verse] = None
    version: Optional[str] = None
    book_mask: int = attrib(init=False)

    def __attrs_post_init__(self) -> None:
        self.book = get_book(self.book)
        self.book_mask = get_book_mask(self.book)

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

    @classmethod
    def from_string(cls, verse: str) -> VerseRange:
        if (match := _search_reference_re.match(verse)) is None:
            raise ReferenceNotUnderstoodError(verse)

        return cls.from_match(match)

    @classmethod
    def from_match(cls, match: Match[str]) -> VerseRange:
        groups = match.groupdict()

        chapter_start_int = int(groups['chapter_start'])
        start = Verse(chapter_start_int, int(groups['verse_start']))

        end = None  # type: Optional[Verse]
        end_str = groups['verse_end']

        if end_str is not None:
            end_int = int(end_str)
            chapter_end_int = chapter_start_int

            chapter_end_str = groups['chapter_end']
            if chapter_end_str is not None:
                chapter_end_int = int(chapter_end_str)

            end = Verse(chapter_end_int, end_int)

        version: Optional[str] = None
        if 'version' in groups:
            version = groups['version']

        return cls(groups['book'], start, end, version)

    @classmethod
    def get_all_from_string(
        cls, string: str, *, only_bracketed: bool = False
    ) -> List[Union[VerseRange, Exception]]:
        ranges: List[Union[VerseRange, Exception]] = []
        lookup_pattern: Pattern[str]

        if only_bracketed:
            lookup_pattern = _bracketed_reference_with_version_re
        else:
            lookup_pattern = _reference_or_bracketed_with_version_re

        if (match := lookup_pattern.search(string)) is not None:
            while match:
                try:
                    ranges.append(cls.from_match(match))
                except Exception as exc:
                    ranges.append(exc)

                match = lookup_pattern.search(string, match.end())

        return ranges

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> VerseRange:
        return cls.from_string(argument)


_truncation_warning: Final = 'The passage was too long and has been truncated:\n\n'
_truncation_warning_len: Final = len(_truncation_warning) + 3


@dataclass(slots=True)
class Passage(object):
    text: str
    range: VerseRange
    version: Optional[str] = None

    @property
    def citation(self) -> str:
        if self.version is not None:
            return f'{self.range} ({self.version})'
        else:
            return str(self.range)

    def get_truncated(self, limit: int) -> str:
        citation = self.citation
        end = limit - (len(citation) + _truncation_warning_len)
        text = self.text[:end]
        return f'{_truncation_warning}{text}\u2026\n\n{citation}'

    def __str__(self) -> str:
        return f'{self.text}\n\n{self.citation}'


@dataclass(slots=True)
class SearchResults(object):
    verses: List[Passage]
    total: int
