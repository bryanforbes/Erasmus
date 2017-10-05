import pytest
from erasmus.data import Verse, VerseRange, Passage, SearchResults
from erasmus.exceptions import ReferenceNotUnderstoodError


class TestVerse(object):
    def test_init(self):
        verse = Verse(1, 1)

        assert verse.chapter == 1
        assert verse.verse == 1

    def test__str__(self):
        verse = Verse(2, 4)

        assert str(verse) == '2:4'

    @pytest.mark.parametrize('verse,expected', [
        (Verse(1, 1), None),
        (Verse(1, 1), Verse(1, 1))
    ])
    def test__eq__(self, verse, expected):
        assert verse == (expected or verse)

    @pytest.mark.parametrize('verse,expected', [
        (Verse(1, 1), {}),
        (Verse(1, 1), Verse(1, 2))
    ])
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

    @pytest.mark.parametrize('passage,expected', [
        (VerseRange('John', Verse(1, 1)), 'John 1:1'),
        (VerseRange('John', Verse(1, 1), Verse(1, 4)), 'John 1:1-4'),
        (VerseRange('John', Verse(1, 1), Verse(2, 2)), 'John 1:1-2:2')
    ])
    def test__str__(self, passage, expected):
        assert str(passage) == expected

    @pytest.mark.parametrize('passage,expected', [
        (VerseRange('John', Verse(1, 1)), None),
        (VerseRange('John', Verse(1, 1)), VerseRange('John', Verse(1, 1)))
    ])
    def test__eq__(self, passage, expected):
        assert passage == (expected or passage)

    @pytest.mark.parametrize('passage,expected', [
        (VerseRange('John', Verse(1, 1)), {}),
        (VerseRange('John', Verse(1, 1)), VerseRange('John', Verse(1, 2)))
    ])
    def test__ne__(self, passage, expected):
        assert passage != expected

    @pytest.mark.parametrize('passage_str,expected,raises', [
        ('1 John 1:1', None, False),
        ('Mark 2:1-4', None, False),
        ('Acts 3:5-6:7', None, False),
        ('asdfc083u4r', None, True),
        ('1 Pet. 3:1', '1 Peter 3:1', False),
        ('1Pet. 3:1 - 4', '1 Peter 3:1-4', False),
        ('1Pet. 3:1- 4', '1 Peter 3:1-4', False),
        ('1Pet 3:1 - 4:5', '1 Peter 3:1-4:5', False),
        ('Isa   54:2   - 23', 'Isaiah 54:2-23', False),
    ])
    def test_from_string(self, passage_str, expected, raises):
        if expected is None:
            expected = passage_str

        if not raises:
            passage = VerseRange.from_string(passage_str)
            assert passage is not None
            assert str(passage) == expected
        else:
            with pytest.raises(ReferenceNotUnderstoodError):
                passage = VerseRange.from_string(passage_str)


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

        assert truncated == f'The passage was too long and has been truncated:\n\n{text[:37]}\u2026\n\nExodus 1:1'

    @pytest.mark.parametrize('passage,expected', [
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')), 'foo bar baz\n\nGenesis 1:2-3'),
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'), 'foo bar baz\n\nGenesis 1:2-3 (KJV)')
    ])
    def test__str__(self, passage, expected):
        assert str(passage) == expected

    @pytest.mark.parametrize('passage,expected', [
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')), None),
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
         Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'))),
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'),
         Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'))
    ])
    def test__eq__(self, passage, expected):
        return passage == (expected or passage)

    @pytest.mark.parametrize('passage,expected', [
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')), {}),
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3')),
         Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-4'))),
        (Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'ESV'),
         Passage('foo bar baz', VerseRange.from_string('Genesis 1:2-3'), 'KJV'))
    ])
    def test__ne__(self, passage, expected):
        return passage != expected


class TestSearchResults(object):
    def test_init(self):
        verses = [VerseRange('Exodus', Verse(1, 1))]
        results = SearchResults(verses, 20)

        assert results.verses == verses
        assert results.total == 20

    @pytest.mark.parametrize('results,expected', [
        (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20), None),
        (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
         SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20))
    ])
    def test__eq__(self, results, expected):
        assert results == (expected or results)

    @pytest.mark.parametrize('results,expected', [
        (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20), {}),
        (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
         SearchResults([VerseRange.from_string('Genesis 1:2-3')], 30)),
        (SearchResults([VerseRange.from_string('Genesis 1:2-3')], 20),
         SearchResults([VerseRange.from_string('Genesis 1:2-4')], 20))
    ])
    def test__ne__(self, results, expected):
        assert results != expected
