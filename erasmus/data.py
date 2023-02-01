from __future__ import annotations

from enum import Flag, auto
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict

import orjson
from attrs import evolve
from botus_receptus import re
from more_itertools import unique_everseen

from .exceptions import (
    BookMappingInvalid,
    BookNotUnderstoodError,
    ReferenceNotUnderstoodError,
)
from .utils import frozen

if TYPE_CHECKING:
    from collections.abc import Iterator
    from re import Match, Pattern
    from typing_extensions import Self

    import discord

    from .types import Bible


class SectionFlag(Flag):
    NONE = 0

    OT = auto()
    Gen = Exod = Lev = Num = Deut = Josh = Judg = Ruth = Sam_1 = Sam_2 = Kgs_1 = OT
    Kgs_2 = Chr_1 = Chr_2 = Ezra = Neh = Esth = Job = Ps = Prov = Eccl = Song = Isa = OT
    Jer = Lam = Ezek = Dan = Hos = Joel = Amos = Obad = Jonah = Mic = Nah = Hab = OT
    Zeph = Hag = Zech = Mal = OT

    NT = auto()
    Matt = Mark = Luke = John = Acts = Rom = Cor_1 = Cor_2 = Gal = Eph = Phil = Col = NT
    Thess_1 = Thess_2 = Tim_1 = Tim_2 = Titus = Phlm = Heb = Jas = Pet_1 = Pet_2 = NT
    John_1 = John_2 = John_3 = Jude = Rev = NT

    Tob = auto()
    Jdt = auto()
    Wis = auto()
    Sir = auto()
    Bar = auto()
    EpJer = auto()
    PrAzar = auto()
    Sus = auto()
    Bel = auto()
    Macc_1 = auto()
    Macc_2 = auto()
    Macc_3 = auto()
    Macc_4 = auto()
    PrMan = auto()
    Esd_1 = auto()
    Esd_2 = auto()
    AddPs = auto()
    EsthGr = auto()
    Odes = auto()
    PssSol = auto()
    DanGr = auto()
    AddEsth = auto()
    AddDan = auto()

    @property
    def book_names(self) -> Iterator[str]:
        for section, book in _book_mask_map.items():
            if section in self:
                match book.name:
                    case 'Genesis':
                        yield 'Old Testament'
                    case 'Matthew':
                        yield 'New Testament'
                    case _:
                        yield book.name

    @classmethod
    def from_book_names(cls, book_names: str, /) -> Self:
        book_mask = SectionFlag.NONE

        if book_names:
            for book_name in book_names.split(','):
                book_name = book_name.strip()
                if book_name == 'OT':
                    book_name = 'Genesis'
                elif book_name == 'NT':
                    book_name = 'Matthew'

                book_mask = book_mask | Book.from_name(book_name).section

        return book_mask


class _RawBookDict(TypedDict):
    name: str
    osis: str
    paratext: str | None
    alt: list[str]


@frozen
class Book:
    name: str
    osis: str
    paratext: str | None
    alt: frozenset[str]
    section: SectionFlag

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_name(cls, name_or_abbr: str, /) -> Self:
        book = _book_map.get(name_or_abbr.lower())

        if book is None:
            raise BookNotUnderstoodError(name_or_abbr)

        return book


def __populate_maps() -> (
    tuple[dict[str, Book], dict[str, Book], dict[SectionFlag, Book]]
):
    book_map: Final[dict[str, Book]] = {}
    osis_map: Final[dict[str, Book]] = {}
    book_mask_map: Final[dict[SectionFlag, Book]] = {}

    with (Path(__file__).resolve().parent / 'data' / 'books.json').open() as f:
        raw_books: list[_RawBookDict] = orjson.loads(f.read())

        for raw_book in raw_books:
            osis: str = raw_book['osis']

            if osis[0].isdecimal():
                section = SectionFlag[f'{osis[1:]}_{osis[0]}']
            else:
                section = SectionFlag[osis]

            book = Book(
                raw_book['name'],
                raw_book['osis'],
                raw_book['paratext'],
                frozenset(raw_book['alt']),
                section,
            )

            if book.section not in book_mask_map:
                book_mask_map[book.section] = book

            osis_map[book.osis] = book

            for input_string in {book.name, book.osis} | book.alt:
                book_map[input_string.lower()] = book

    return book_map, osis_map, book_mask_map


_book_map, _osis_map, _book_mask_map = __populate_maps()

_book_map: Final
_osis_map: Final
_book_mask_map: Final


@frozen
class Verse:
    chapter: int
    verse: int

    def __str__(self, /) -> str:
        return f'{self.chapter}:{self.verse}'


# Inspired by
# https://github.com/TehShrike/verse-reference-regex/blob/master/create-regex.js
_book_re: Final = re.compile(
    re.named_group('book')(
        re.either(*re.escape_all(unique_everseen(_book_map.keys())))
    ),
    re.optional(re.DOT),
)

_version_group: Final = re.named_group('version')
_one_or_more_digit: Final = re.one_or_more(re.DIGIT)
_colon: Final = re.combine(
    re.any_number_of(re.WHITESPACE), ':', re.any_number_of(re.WHITESPACE)
)

_reference_re: Final = re.compile(
    _book_re,
    re.one_or_more(re.WHITESPACE),
    re.named_group('chapter_start')(_one_or_more_digit),
    _colon,
    re.named_group('verse_start')(_one_or_more_digit),
    re.optional(
        re.any_number_of(re.WHITESPACE),
        '[',
        re.DASH,
        '\u2013',
        '\u2014',
        ']',
        re.any_number_of(re.WHITESPACE),
        re.optional(re.named_group('chapter_end')(_one_or_more_digit), _colon),
        re.named_group('verse_end')(_one_or_more_digit),
    ),
    flags=re.IGNORECASE,
)

_reference_with_version_re: Final = re.compile(
    _reference_re,
    re.optional(
        re.any_number_of(re.WHITESPACE),
        _version_group(re.one_or_more(re.ALPHANUMERICS)),
    ),
    flags=re.IGNORECASE,
)

_reference_or_bracketed_with_version_re: Final = re.compile(
    re.optional(
        re.named_group('bracket')(re.LEFT_BRACKET, re.any_number_of(re.WHITESPACE))
    ),
    _reference_re,
    re.if_group(
        'bracket',
        re.group(
            re.optional(
                re.one_or_more(re.WHITESPACE),
                _version_group(re.one_or_more(re.ALPHANUMERICS)),
            ),
            re.any_number_of(re.WHITESPACE),
            re.RIGHT_BRACKET,
        ),
    ),
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

_search_reference_with_version_re: Final = re.compile(
    re.START, _reference_with_version_re, re.END, flags=re.IGNORECASE
)


@frozen
class VerseRange:
    book: Book
    start: Verse
    end: Verse | None
    version: str | None

    @property
    def book_mask(self) -> SectionFlag:
        return self.book.section

    @property
    def osis(self) -> str:
        return self.book.osis

    @property
    def paratext(self) -> str | None:
        return self.book.paratext

    @property
    def verses(self, /) -> str:
        verse = str(self.start)

        if self.end is not None:
            if self.end.chapter == self.start.chapter:
                verse += f'-{self.end.verse}'
            else:
                verse += f'-{self.end}'

        return verse

    def for_bible(self, bible: Bible, /) -> Self:
        if bible.book_mapping is not None and self.osis in bible.book_mapping:
            osis = bible.book_mapping[self.osis]
            book = _osis_map.get(osis)

            if book is None:
                raise BookMappingInvalid(bible.name, self.book, osis)

            return evolve(self, book=book)

        return self

    def with_version(self, version: str | None, /) -> Self:
        return evolve(self, version=version)

    def __str__(self, /) -> str:
        return f'{self.book} {self.verses}'

    @classmethod
    def create(
        cls,
        book: str,
        start: Verse,
        end: Verse | None = None,
        version: str | None = None,
        /,
    ) -> Self:
        return cls(
            Book.from_name(book),
            start,
            end,
            version,
        )

    @classmethod
    def from_string(cls, verse: str, /) -> Self:
        if (match := _search_reference_re.match(verse)) is None:
            raise ReferenceNotUnderstoodError(verse)

        return cls.from_match(match)

    @classmethod
    def from_string_with_version(cls, verse: str, /) -> Self:
        if (match := _search_reference_with_version_re.match(verse)) is None:
            raise ReferenceNotUnderstoodError(verse)

        return cls.from_match(match)

    @classmethod
    def from_match(cls, match: Match[str], /) -> Self:
        groups = match.groupdict()

        chapter_start_int = int(groups['chapter_start'])
        start = Verse(chapter_start_int, int(groups['verse_start']))

        end: Verse | None = None
        end_str = groups['verse_end']

        if end_str is not None:
            end_int = int(end_str)
            chapter_end_int = chapter_start_int

            chapter_end_str = groups['chapter_end']
            if chapter_end_str is not None:
                chapter_end_int = int(chapter_end_str)

            end = Verse(chapter_end_int, end_int)

        version: str | None = groups.get('version')

        return cls.create(groups['book'], start, end, version)

    @classmethod
    def get_all_from_string(
        cls, string: str, /, *, only_bracketed: bool = False
    ) -> list[Self | Exception]:
        ranges: list[VerseRange | Exception] = []
        lookup_pattern: Pattern[str]

        if only_bracketed:
            lookup_pattern = _bracketed_reference_with_version_re
        else:
            lookup_pattern = _reference_or_bracketed_with_version_re

        if (match := lookup_pattern.search(string)) is not None:
            while match:
                try:
                    ranges.append(cls.from_match(match))
                except Exception as exc:  # noqa: PIE786
                    ranges.append(exc)

                match = lookup_pattern.search(string, match.end())

        return ranges

    @classmethod
    async def transform(cls, itx: discord.Interaction, value: str, /) -> Self:
        return cls.from_string_with_version(value)


@frozen
class Passage:
    text: str
    range: VerseRange
    version: str | None = None

    @property
    def citation(self, /) -> str:
        if self.version is not None:
            return f'{self.range} ({self.version})'
        else:
            return str(self.range)

    def __str__(self, /) -> str:
        return f'{self.text}\n\n{self.citation}'


@frozen
class SearchResults:
    verses: list[Passage]
    total: int

    def __iter__(self, /) -> Iterator[Passage]:
        yield from self.verses
