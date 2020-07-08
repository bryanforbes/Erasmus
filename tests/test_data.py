import pytest

from erasmus.data import Passage, SearchResults, Verse, VerseRange
from erasmus.exceptions import ReferenceNotUnderstoodError


class TestVerse(object):
    def test_init(self):
        verse = Verse(1, 1)

        assert verse.chapter == 1
        assert verse.verse == 1

    def test__str__(self):
        verse = Verse(2, 4)

        assert str(verse) == '2:4'

    @pytest.mark.parametrize(
        'verse,expected', [(Verse(1, 1), None), (Verse(1, 1), Verse(1, 1))]
    )
    def test__eq__(self, verse, expected):
        assert verse == (expected or verse)

    @pytest.mark.parametrize(
        'verse,expected', [(Verse(1, 1), {}), (Verse(1, 1), Verse(1, 2))]
    )
    def test__ne__(self, verse, expected):
        assert verse != expected


class TestVerseRange(object):
    def test_init(self):
        verse_start = Verse(1, 1)
        verse_end = Verse(1, 4)

        passage = VerseRange('John', verse_start, verse_end)

        assert passage.book == 'John'
        assert passage.start == verse_start
        assert passage.end == verse_end

        passage = VerseRange('John', verse_start)
        assert passage.book == 'John'
        assert passage.start == verse_start
        assert passage.end is None

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange('John', Verse(1, 1)), 'John 1:1'),
            (VerseRange('John', Verse(1, 1), Verse(1, 4)), 'John 1:1-4'),
            (VerseRange('John', Verse(1, 1), Verse(2, 2)), 'John 1:1-2:2'),
        ],
    )
    def test__str__(self, passage, expected):
        assert str(passage) == expected

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange('John', Verse(1, 1)), None),
            (VerseRange('John', Verse(1, 1)), VerseRange('John', Verse(1, 1))),
            (
                VerseRange('John', Verse(1, 1), Verse(2, 1)),
                VerseRange('John', Verse(1, 1), Verse(2, 1)),
            ),
            (
                VerseRange('John', Verse(1, 1), Verse(2, 1), 'sbl'),
                VerseRange('John', Verse(1, 1), Verse(2, 1), 'sbl'),
            ),
        ],
    )
    def test__eq__(self, passage, expected):
        assert passage == (expected or passage)

    @pytest.mark.parametrize(
        'passage,expected',
        [
            (VerseRange('John', Verse(1, 1)), {}),
            (VerseRange('John', Verse(1, 1)), VerseRange('John', Verse(1, 2))),
            (
                VerseRange('John', Verse(1, 1), Verse(2, 1)),
                VerseRange('John', Verse(1, 1), Verse(3, 1)),
            ),
            (
                VerseRange('John', Verse(1, 1), Verse(2, 1), 'sbl'),
                VerseRange('John', Verse(1, 1), Verse(2, 1), 'niv'),
            ),
        ],
    )
    def test__ne__(self, passage, expected):
        assert passage != expected

    @pytest.mark.parametrize(
        'passage_str,expected',
        [
            ('1 John 1:1', None),
            ('Mark 2:1-4', None),
            ('Acts 3:5-6:7', None),
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
    def test_from_string(self, passage_str, expected):
        if expected is None:
            expected = passage_str

        passage = VerseRange.from_string(passage_str)
        assert passage is not None
        assert str(passage) == expected

    @pytest.mark.parametrize(
        'passage_str,expected',
        [
            ('foo 1 John 1:1 bar', [[VerseRange('1 John', Verse(1, 1))], []]),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 baz',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1\u20134 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1\u20144 baz Acts 3:5-6:7',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark    2 : 1   -     4 baz [Acts 3:5-6:7]',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [VerseRange('Acts', Verse(3, 5), Verse(6, 7))],
                ],
            ),
            (
                'foo 1 John 1:1 bar [Mark 2:1-4 KJV] baz Acts 3:5-6:7 blah',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [VerseRange('Mark', Verse(2, 1), Verse(2, 4), 'KJV')],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 KJV baz [Acts 3:5-6:7 sbl123] blah',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7), 'sbl123'),
                    ],
                    [VerseRange('Acts', Verse(3, 5), Verse(6, 7), 'sbl123')],
                ],
            ),
            (
                'foo 1 John 1:1 bar Mark 2:1-4 KJV baz [Acts 3:5-6:7 sbl 123] blah',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4)),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [],
                ],
            ),
            (
                'foo [ 1 John 1:1 ] bar [Mark 2:1-4 KJV ] baz [Acts 3:5-6:7 sbl 123 ] '
                'blah',
                [
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                        VerseRange('Acts', Verse(3, 5), Verse(6, 7)),
                    ],
                    [
                        VerseRange('1 John', Verse(1, 1)),
                        VerseRange('Mark', Verse(2, 1), Verse(2, 4), 'KJV'),
                    ],
                ],
            ),
            # ('foo 1 John 1:1 bar', {'brackets': True}, []),
            # ('foo [1 John 1:1] bar', {'brackets': True}, ['1 John 1:1']),
            # ('foo 1 John 1:1 bar [Mark 2:1-4] baz', {'brackets': True}, ['Mark 2:1-4']),  # noqa
            # (
            #     'foo [1 John 1:1] bar [Mark 2:1-4] baz',
            #     {'brackets': True},
            #     ['1 John 1:1', 'Mark 2:1-4'],
            # ),
            # (
            #     'foo [1 John 1:1] bar Mark 2:1-4 baz [Acts 3:5-6:7]',
            #     {'brackets': True},
            #     ['1 John 1:1', 'Acts 3:5-6:7'],
            # ),
            # (
            #     'foo [1 John 1:1] bar [Mark 2:1-4] baz [Acts 3:5-6:7]',
            #     {'brackets': True},
            #     ['1 John 1:1', 'Mark 2:1-4', 'Acts 3:5-6:7'],
            # ),
        ],
    )
    @pytest.mark.parametrize('only_bracketed', [False, True])
    def test_get_all_from_string_optional(self, passage_str, only_bracketed, expected):
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

    @pytest.mark.parametrize(
        'passage_str', ['asdfc083u4r', 'Gen 1', 'Gen 1:', 'Gen 1:1 -', 'Gen 1:1 - 2:']
    )
    def test_from_string_raises(self, passage_str):
        with pytest.raises(ReferenceNotUnderstoodError):
            VerseRange.from_string(passage_str)


class TestPassage(object):
    def test_init(self):
        text = 'foo bar baz'
        range = VerseRange('Exodus', Verse(1, 1))
        passage = Passage(text, range)

        assert passage.text == text
        assert passage.range == range
        assert passage.version is None

    def test_get_truncated(self):
        text = 'foo bar baz' * 10
        range = VerseRange('Exodus', Verse(1, 1))
        passage = Passage(text, range)

        truncated = passage.get_truncated(100)

        assert (
            truncated
            == f'The passage was too long and has been truncated:\n\n{text[:37]}'
            '\u2026\n\nExodus 1:1'
        )

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
    def test__str__(self, passage, expected):
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
    def test__eq__(self, passage, expected):
        return passage == (expected or passage)

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
    def test__ne__(self, passage, expected):
        return passage != expected


class TestSearchResults(object):
    def test_init(self):
        verses = [VerseRange('Exodus', Verse(1, 1))]
        results = SearchResults(verses, 20)

        assert results.verses == verses
        assert results.total == 20

    @pytest.mark.parametrize(
        'results,expected',
        [
            (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20), None),
            (
                SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
                SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
            ),
        ],
    )
    def test__eq__(self, results, expected):
        assert results == (expected or results)

    @pytest.mark.parametrize(
        'results,expected',
        [
            (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20), {}),
            (
                SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
                SearchResults([VerseRange.from_string('Genesis 1:2-3')], 30),
            ),
            (
                SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
                SearchResults([VerseRange.from_string('Genesis 1:2-4')], 20),
            ),
        ],
    )
    def test__ne__(self, results, expected):
        assert results != expected
