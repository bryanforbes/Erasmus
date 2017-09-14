import pytest
from erasmus.data import Verse, Passage, SearchResults


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


class TestPassage(object):
    def test_init(self):
        verse_start = Verse(1, 1)
        verse_end = Verse(1, 4)

        passage = Passage('John', verse_start, verse_end)

        assert passage.book == 'John'
        assert passage.start == verse_start
        assert passage.end == verse_end

        passage = Passage('John', verse_start)
        assert passage.book == 'John'
        assert passage.start == verse_start
        assert passage.end is None

    @pytest.mark.parametrize('passage,expected', [
        (Passage('John', Verse(1, 1)), 'John 1:1'),
        (Passage('John', Verse(1, 1), Verse(1, 4)), 'John 1:1-4'),
        (Passage('John', Verse(1, 1), Verse(2, 2)), 'John 1:1-2:2')
    ])
    def test__str__(self, passage, expected):
        assert str(passage) == expected

    @pytest.mark.parametrize('passage,expected', [
        (Passage('John', Verse(1, 1)), None),
        (Passage('John', Verse(1, 1)), Passage('John', Verse(1, 1)))
    ])
    def test__eq__(self, passage, expected):
        assert passage == (expected or passage)

    @pytest.mark.parametrize('passage,expected', [
        (Passage('John', Verse(1, 1)), {}),
        (Passage('John', Verse(1, 1)), Passage('John', Verse(1, 2)))
    ])
    def test__ne__(self, passage, expected):
        assert passage != expected

    @pytest.mark.parametrize('passage_str,should_be_str', [
        ('1 John 1:1', True),
        ('Mark 2:1-4', True),
        ('Acts 3:5-6:7', True),
        ('asdfc083u4r', False),
    ])
    def test_from_string(self, passage_str, should_be_str):
        passage = Passage.from_string(passage_str)

        if should_be_str:
            assert str(passage) == passage_str
        else:
            assert passage is None


class TestSearchResults(object):
    def test_init(self):
        verses = [Passage('book', Verse(1, 1))]
        results = SearchResults(verses, 20)

        assert results.verses == verses
        assert results.total == 20

    @pytest.mark.parametrize('results,expected', [
        (SearchResults([Passage.from_string('book 1:2-3')], 20), None),
        (SearchResults([Passage.from_string('book 1:2-3')], 20), SearchResults([Passage.from_string('book 1:2-3')], 20))
    ])
    def test__eq__(self, results, expected):
        assert results == (expected or results)

    @pytest.mark.parametrize('results,expected', [
        (SearchResults([Passage.from_string('book 1:2-3')], 20), {}),
        (SearchResults([Passage.from_string('book 1:2-3')], 20),
         SearchResults([Passage.from_string('book 1:2-3')], 30)),
        (SearchResults([Passage.from_string('book 1:2-3')], 20),
         SearchResults([Passage.from_string('book 1:2-4')], 20))
    ])
    def test__ne__(self, results, expected):
        assert results != expected
