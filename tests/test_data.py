from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Any, TypedDict

import orjson
import pytest

from erasmus import data
from erasmus.data import Book, Passage, SearchResults, SectionFlag, Verse, VerseRange
from erasmus.exceptions import BookNotUnderstoodError, ReferenceNotUnderstoodError


class _RawBookDict(TypedDict):
    name: str
    osis: str
    paratext: str | None
    alt: list[str]


with (Path(data.__file__).parent.resolve() / 'data' / 'books.json').open() as f:
    _book_data: list[_RawBookDict] = orjson.loads(f.read())


class TestSectionFlag:
    def test_book_names(self) -> None:
        assert list(SectionFlag.NONE.book_names) == []
        assert list((SectionFlag.NONE | SectionFlag.John).book_names) == [
            'New Testament'
        ]
        assert list((SectionFlag.OT | SectionFlag.NT).book_names) == [
            'Old Testament',
            'New Testament',
        ]
        assert list(
            (
                SectionFlag.Tob | SectionFlag.Jdt | SectionFlag.Wis | SectionFlag.Macc_1
            ).book_names
        ) == ['Tobit', 'Judith', 'Wisdom', '1 Maccabees']

    @pytest.mark.parametrize(
        'book_name,expected_section',
        [
            (
                book['name'].upper(),
                SectionFlag[
                    book['osis']
                    if not book['osis'][0].isdecimal()
                    else f'{book["osis"][1:]}_{book["osis"][0]}'
                ],
            )
            for book in _book_data
        ],
    )
    def test_from_book_names(
        self, book_name: str, expected_section: SectionFlag
    ) -> None:
        assert SectionFlag.from_book_names(book_name) == expected_section

    @pytest.mark.parametrize(
        'book_name,expected_section',
        [
            ('OT', SectionFlag.OT),
            ('NT', SectionFlag.NT),
            ('', SectionFlag.NONE),
        ],
    )
    def test_from_book_names_special(
        self, book_name: str, expected_section: SectionFlag
    ) -> None:
        assert SectionFlag.from_book_names(book_name) == expected_section

    def test_from_book_names_raises(self) -> None:
        with pytest.raises(BookNotUnderstoodError):
            SectionFlag.from_book_names('NONE')


class TestBook:
    @pytest.mark.parametrize(
        'book_name,expected_osis',
        list(
            chain.from_iterable(
                [
                    (name, book['osis'])
                    for name in ([book['name'], book['osis']] + book['alt'])
                ]
                for book in _book_data
            )
        ),
    )
    def test_from_name(self, book_name: str, expected_osis: str) -> None:
        assert Book.from_name(book_name).osis == expected_osis


class TestVerse:
    def test_init(self) -> None:
        verse = Verse(1, 1)

        assert verse.chapter == 1
        assert verse.verse == 1

    def test__str__(self) -> None:
        verse = Verse(2, 4)

        assert str(verse) == '2:4'

    @pytest.mark.parametrize(
        'verse,expected', [(Verse(1, 1), None), (Verse(1, 1), Verse(1, 1))]
    )
    def test__eq__(self, verse: Verse, expected: Verse | None) -> None:
        assert verse == (expected or verse)

    @pytest.mark.parametrize(
        'verse,expected', [(Verse(1, 1), {}), (Verse(1, 1), Verse(1, 2))]
    )
    def test__ne__(self, verse: Verse, expected: Any) -> None:
        assert verse != expected


class TestVerseRange:
    def test_create(self) -> None:
        verse_start = Verse(1, 1)
        verse_end = Verse(1, 4)

        passage = VerseRange.create('John', verse_start, verse_end)

        assert passage.book.name == 'John'
        assert passage.osis == 'John'
        assert passage.paratext == 'JHN'
        assert passage.book_mask == SectionFlag.John
        assert passage.start == verse_start
        assert passage.end == verse_end

        passage = VerseRange.create('Genesis', verse_start)
        assert passage.book.name == 'Genesis'
        assert passage.osis == 'Gen'
        assert passage.paratext == 'GEN'
        assert passage.book_mask == SectionFlag.OT
        assert passage.start == verse_start
        assert passage.end is None

    def test_create_raises(self) -> None:
        with pytest.raises(BookNotUnderstoodError):
            VerseRange.create('asdf', Verse(1, 1))

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange.create('John', Verse(1, 1)), 'John 1:1'),
            (VerseRange.create('John', Verse(1, 1), Verse(1, 4)), 'John 1:1-4'),
            (VerseRange.create('John', Verse(1, 1), Verse(2, 2)), 'John 1:1-2:2'),
        ],
    )
    def test__str__(self, passage: VerseRange, expected: str) -> None:
        assert str(passage) == expected

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange.create('John', Verse(1, 1)), None),
            (
                VerseRange.create('John', Verse(1, 1)),
                VerseRange.create('John', Verse(1, 1)),
            ),
            (
                VerseRange.create('John', Verse(1, 1), Verse(2, 1)),
                VerseRange.create('John', Verse(1, 1), Verse(2, 1)),
            ),
            (
                VerseRange.create('John', Verse(1, 1), Verse(2, 1), 'sbl'),
                VerseRange.create('John', Verse(1, 1), Verse(2, 1), 'sbl'),
            ),
        ],
    )
    def test__eq__(self, passage: VerseRange, expected: VerseRange | None) -> None:
        assert passage == (expected or passage)

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange.create('John', Verse(1, 1)), {}),
            (
                VerseRange.create('John', Verse(1, 1)),
                VerseRange.create('John', Verse(1, 2)),
            ),
            (
                VerseRange.create('John', Verse(1, 1), Verse(2, 1)),
                VerseRange.create('John', Verse(1, 1), Verse(3, 1)),
            ),
            (
                VerseRange.create('John', Verse(1, 1), Verse(2, 1), 'sbl'),
                VerseRange.create('John', Verse(1, 1), Verse(2, 1), 'niv'),
            ),
        ],
    )
    def test__ne__(self, passage: VerseRange, expected: Any) -> None:
        assert passage != expected

    @pytest.mark.parametrize(
        'passage_str,expected',
        [
            ('1 John 1:1', '1 John 1:1'),
            ('Mark 2:1-4', 'Mark 2:1-4'),
            ('Acts 3:5-6:7', 'Acts 3:5-6:7'),
            ('Mark 2:1\u20134', 'Mark 2:1-4'),
            ('Mark 2:1\u20144', 'Mark 2:1-4'),
            ('1 Pet. 3:1', '1 Peter 3:1'),
            ('1Pet. 3:1 - 4', '1 Peter 3:1-4'),
            ('1Pet. 3:1- 4', '1 Peter 3:1-4'),
            ('1Pet 3:1 - 4:5', '1 Peter 3:1-4:5'),
            ('Isa   54:2   - 23', 'Isaiah 54:2-23'),
            ('1 Pet. 3 : 1', '1 Peter 3:1'),
            ('1Pet. 3 : 1 - 4', '1 Peter 3:1-4'),
            ('1Pet. 3 : 1- 4', '1 Peter 3:1-4'),
            ('1Pet 3 : 1 - 4 : 5', '1 Peter 3:1-4:5'),
            ('Isa   54 : 2   - 23', 'Isaiah 54:2-23'),
        ],
    )
    def test_from_string(self, passage_str: str, expected: str) -> None:
        passage = VerseRange.from_string(passage_str)
        assert passage is not None
        assert str(passage) == expected

    @pytest.mark.parametrize(
        'passage_str', ['asdfc083u4r', 'Gen 1', 'Gen 1:', 'Gen 1:1 -', 'Gen 1:1 - 2:']
    )
    def test_from_string_raises(self, passage_str: str) -> None:
        with pytest.raises(ReferenceNotUnderstoodError):
            VerseRange.from_string(passage_str)

    @pytest.mark.parametrize(
        'passage_str,expected_range,expected_version',
        [
            ('1 John 1:1', '1 John 1:1', None),
            ('Mark 2:1-4 qwer', 'Mark 2:1-4', 'qwer'),
            ('Acts 3:5-6:7 asdf', 'Acts 3:5-6:7', 'asdf'),
            ('Mark 2:1\u20134 qwer', 'Mark 2:1-4', 'qwer'),
            ('Mark 2:1\u20144 asdf', 'Mark 2:1-4', 'asdf'),
            ('1 Pet. 3:1    qwer', '1 Peter 3:1', 'qwer'),
            ('1Pet. 3:1 - 4   asdf', '1 Peter 3:1-4', 'asdf'),
            ('1Pet. 3:1- 4      qwer', '1 Peter 3:1-4', 'qwer'),
            ('1Pet 3:1 - 4:5   asdf', '1 Peter 3:1-4:5', 'asdf'),
            ('Isa   54:2   - 23   qwer', 'Isaiah 54:2-23', 'qwer'),
            ('1 Pet. 3 : 1      asdf', '1 Peter 3:1', 'asdf'),
            ('1Pet. 3 : 1 - 4   qwer', '1 Peter 3:1-4', 'qwer'),
            ('1Pet. 3 : 1- 4      asdf', '1 Peter 3:1-4', 'asdf'),
            ('1Pet 3 : 1 - 4 : 5   qwer', '1 Peter 3:1-4:5', 'qwer'),
            ('Isa   54 : 2   - 23      asdf', 'Isaiah 54:2-23', 'asdf'),
        ],
    )
    def test_from_string_with_version(
        self, passage_str: str, expected_range: str, expected_version: str | None
    ) -> None:
        passage = VerseRange.from_string_with_version(passage_str)
        assert passage is not None
        assert str(passage) == expected_range
        assert passage.version == expected_version

    @pytest.mark.parametrize(
        'passage_str',
        [
            'asdfc083u4r',
            'Gen 1',
            'Gen 1:',
            'Gen 1:1 -',
            'Gen 1:1 - 2:',
            'Gen 1:1 asdf qwer',
        ],
    )
    def test_from_string_with_version_raises(self, passage_str: str) -> None:
        with pytest.raises(ReferenceNotUnderstoodError):
            VerseRange.from_string_with_version(passage_str)

    @pytest.mark.parametrize(
        'passage_str,expected',
        [
            ('foo 1 John 1:1 bar', [[VerseRange.create('1 John', Verse(1, 1))], []]),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 baz',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1\u20134 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1\u20144 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark    2 : 1   -     4 baz [Acts 3:5-6:7]',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [VerseRange.create('Acts', Verse(3, 5), Verse(6, 7))],
                ],
            ),
            (
                'foo 1 John 1:1 bar [Mark 2:1-4 KJV] baz Acts 3:5-6:7 blah',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [VerseRange.create('Mark', Verse(2, 1), Verse(2, 4), 'KJV')],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 KJV baz [Acts 3:5-6:7 sbl123] blah',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7), 'sbl123'),
                    ],
                    [VerseRange.create('Acts', Verse(3, 5), Verse(6, 7), 'sbl123')],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 KJV baz [Acts 3:5-6:7 sbl 123] blah',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo [ 1 John 1:1 ] bar [Mark 2:1-4  KJV ] baz [Acts 3:5-6:7 sbl 123 ] '
                'blah',
                [
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                        VerseRange.create('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [
                        VerseRange.create('1 John', Verse(1, 1)),
                        VerseRange.create('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                    ],
                ],
            ),
        ],
    )
    @pytest.mark.parametrize('only_bracketed', [False, True])
    def test_get_all_from_string(
        self, passage_str: str, only_bracketed: bool, expected: list[list[VerseRange]]
    ) -> None:
        passages = VerseRange.get_all_from_string(
            passage_str, only_bracketed=only_bracketed
        )
        assert passages is not None

        index: int
        if only_bracketed:
            index = 1
        else:
            index = 0

        assert passages == expected[index]


class TestPassage:
    def test_init(self) -> None:
        text = 'foo bar baz'
        range = VerseRange.create('Exodus', Verse(1, 1))
        passage = Passage(text, range)

        assert passage.text == text
        assert passage.range == range
        assert passage.version is None

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
                'foo bar baz\n\nGenesis 1:2-3',
            ),
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'),
                'foo bar baz\n\nGenesis 1:2-3 (KJV)',
            ),
        ],
    )
    def test__str__(self, passage: Passage, expected: str) -> None:
        assert str(passage) == expected

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')), None),
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
            ),
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'),
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'),
            ),
        ],
    )
    def test__eq__(self, passage: Passage, expected: Passage | None) -> None:
        assert passage == (expected or passage)

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')), {}),
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-4')),
            ),
            (
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'ESV'),
                Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'),
            ),
        ],
    )
    def test__ne__(self, passage: Passage, expected: Any) -> None:
        assert passage != expected


class TestSearchResults:
    def test_init(self) -> None:
        verses = [Passage('asdf', VerseRange.create('Exodus', Verse(1, 1)))]
        results = SearchResults(verses, 20)

        assert results.verses == verses
        assert results.total == 20

    @pytest.mark.parametrize(
        'results,expected',
        [
            (
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
                None,
            ),
            (
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
            ),
        ],
    )
    def test__eq__(
        self, results: SearchResults, expected: SearchResults | None
    ) -> None:
        assert results == (expected or results)

    @pytest.mark.parametrize(
        'results,expected',
        [
            (
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
                {},
            ),
            (
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 30
                ),
            ),
            (
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-3'))], 20
                ),
                SearchResults(
                    [Passage('asdf', VerseRange.from_string('Genesis 1:2-4'))], 20
                ),
            ),
        ],
    )
    def test__ne__(self, results: SearchResults, expected: Any) -> None:
        assert results != expected

    def test__iter__(self) -> None:
        passages = [
            Passage('asdf', VerseRange.from_string('Genesis 1:2-3')),
            Passage('asdf2', VerseRange.from_string('Genesis 1:8-10')),
        ]
        results = SearchResults(passages, 20)

        assert list(results) == passages
