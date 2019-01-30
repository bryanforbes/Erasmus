from __future__ import annotations

from typing import Optional, Union, List, Dict, Pattern, Match, TYPE_CHECKING
import attr
from pathlib import Path
from itertools import chain
from mypy_extensions import TypedDict
from more_itertools import unique_everseen
from botus_receptus import re
from .json import load
from .exceptions import BookNotUnderstoodError, ReferenceNotUnderstoodError

if TYPE_CHECKING:
    from .context import Context


class BookDict(TypedDict):
    name: str
    osis: str
    alt: List[str]
    section: int


with (Path(__file__).resolve().parent / 'data' / 'books.json').open() as f:
    books_data: List[BookDict] = load(f)

# Inspired by
# https://github.com/TehShrike/verse-reference-regex/blob/master/create-regex.js
_book_re = re.compile(
    re.named_group('book')(
        re.either(
            *re.escape_all(
                unique_everseen(
                    chain.from_iterable(
                        [
                            [book['name'], book['osis']] + book['alt']
                            for book in books_data
                        ]
                    )
                )
            )
        )
    ),
    re.optional(re.DOT),
)

_chapter_start_group = re.named_group('chapter_start')
_chapter_end_group = re.named_group('chapter_end')
_verse_start_group = re.named_group('verse_start')
_verse_end_group = re.named_group('verse_end')
_version_group = re.named_group('version')
_one_or_more_digit = re.one_or_more(re.DIGIT)
_colon = re.combine(
    re.any_number_of(re.WHITESPACE), ':', re.any_number_of(re.WHITESPACE)
)

_reference_re = re.compile(
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

_reference_with_version_re = re.compile(
    _reference_re,
    re.optional(
        re.group(
            re.any_number_of(re.WHITESPACE),
            _version_group(re.one_or_more(re.ALPHANUMERICS)),
        )
    ),
    flags=re.IGNORECASE,
)

_reference_or_bracketed_with_version_re = re.compile(
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

_bracketed_reference_with_version_re = re.compile(
    re.LEFT_BRACKET,
    re.any_number_of(re.WHITESPACE),
    _reference_with_version_re,
    re.any_number_of(re.WHITESPACE),
    re.RIGHT_BRACKET,
    flags=re.IGNORECASE,
)

_search_reference_re = re.compile(re.START, _reference_re, re.END, flags=re.IGNORECASE)

_book_input_map: Dict[str, str] = {}
_book_mask_map: Dict[str, int] = {}
for _book in books_data:
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


@attr.s(slots=True, auto_attribs=True)
class Verse(object):
    chapter: int
    verse: int

    def __str__(self) -> str:
        return f'{self.chapter}:{self.verse}'


@attr.s(slots=True, auto_attribs=True)
class VerseRange(object):
    book: str = attr.ib(converter=get_book)
    start: Verse
    end: Optional[Verse] = None
    version: Optional[str] = None
    book_mask: int = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
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
        match = _search_reference_re.match(verse)

        if match is None:
            raise ReferenceNotUnderstoodError(verse)

        return cls.from_match(match)

    @classmethod
    def from_match(cls, match: Match) -> VerseRange:
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

        match = lookup_pattern.search(string)

        if match:
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


truncation_warning = 'The passage was too long and has been truncated:\n\n'
truncation_warning_len = len(truncation_warning) + 3


@attr.s(slots=True, auto_attribs=True)
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
        end = limit - (len(citation) + truncation_warning_len)
        text = self.text[:end]
        return f'{truncation_warning}{text}\u2026\n\n{citation}'

    def __str__(self) -> str:
        return f'{self.text}\n\n{self.citation}'


@attr.s(slots=True, auto_attribs=True)
class SearchResults(object):
    verses: List[Passage]
    total: int
