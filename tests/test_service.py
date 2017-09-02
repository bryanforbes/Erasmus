import pytest
from erasmus.service import Service, Passage, SearchResults


class TestPassage(object):
    def test_init(self):
        passage = Passage('book', 1, 2, 3)
        assert passage.book == 'book'
        assert passage.chapter == 1
        assert passage.verse_start == 2
        assert passage.verse_end == 3

        passage = Passage('book', 1, 2)
        assert passage.book == 'book'
        assert passage.chapter == 1
        assert passage.verse_start == 2
        assert passage.verse_end == -1

    def test__str__(self):
        passage = Passage('book', 1, 2)
        assert str(passage) == 'book 1:2'

        passage = Passage('book', 1, 2, 3)
        assert str(passage) == 'book 1:2-3'

    def test_from_string(self):
        passage = Passage.from_string('1 Timothy 5:8-9')
        assert passage.book == '1 Timothy'
        assert passage.chapter == 5
        assert passage.verse_start == 8
        assert passage.verse_end == 9

        passage = Passage.from_string('1 Timothy 5:8')
        assert passage.book == '1 Timothy'
        assert passage.chapter == 5
        assert passage.verse_start == 8
        assert passage.verse_end == -1

        passage = Passage.from_string('foo bar baz')
        assert passage is None

    def test__eq__(self):
        passage = Passage.from_string('1 Timothy 5:8-9')
        assert passage != {}
        assert passage == Passage.from_string('1 Timothy 5:8-9')
        assert passage == passage


class TestSearchResults(object):
    def test_init(self):
        verses = [Passage('book', 1, 2, 3)]
        results = SearchResults(verses, 20)

        assert results.verses == verses
        assert results.total == 20

    def test__eq__(self):
        verses = [Passage('book', 1, 2, 3)]
        results = SearchResults(verses, 20)

        assert results != {}
        assert results == results
        assert results == SearchResults([Passage('book', 1, 2, 3)], 20)


@pytest.mark.usefixtures('mock_aiohttp')
class TestService(object):
    def test_init(self):
        config = {}
        service = Service(config)
        assert service.config is config

    @pytest.mark.asyncio
    async def test_get_passage(self, mocker):
        service = Service({})
        passage = Passage('book', 1, 2, 3)

        mocker.patch.object(service, '_parse_passage',
                            return_value='John 1:1-4')
        mocker.spy(service, '_get_passage')

        with pytest.raises(NotImplementedError):
            await service.get_passage('version', passage)

        assert service._parse_passage.call_count == 1
        assert service._parse_passage.call_args == mocker.call(passage)
        assert service._get_passage.call_count == 1
        assert service._get_passage.call_args == mocker.call('version', 'John 1:1-4')

    @pytest.mark.asyncio
    async def test_search(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service.search('version', ['one', 'two', 'three'])

    def test__parse_passage(self):
        service = Service({})
        passage = Passage('book', 1, 2, 3)

        with pytest.raises(NotImplementedError):
            service._parse_passage(passage)

    @pytest.mark.asyncio
    async def test__get_passage(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service._get_passage('version', 'passage')

    @pytest.mark.asyncio
    async def test__get(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service._get('/foo/bar/baz')
