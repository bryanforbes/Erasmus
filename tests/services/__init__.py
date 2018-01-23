import pytest
from erasmus.data import VerseRange, Passage, SearchResults, Bible
from erasmus.exceptions import DoNotUnderstandError

Galatians_3_10_11 = ('**10.** For as many as are of the works of the Law are under a '
                     'curse; for it is written, “CURSED IS EVERYONE WHO DOES NOT '
                     'ABIDE BY ALL THINGS WRITTEN IN THE BOOK OF THE LAW, TO '
                     'PERFORM THEM.” **11.** Now that no one is justified by the Law '
                     'before God is evident; for, “THE RIGHTEOUS MAN SHALL LIVE BY '
                     'FAITH.”')

Mark_5_1 = '**1.** They came to the other side of the sea, into the country of the Gerasenes.'


@pytest.mark.usefixtures('mock_aiohttp')
class ServiceTest(object):
    @pytest.fixture
    def service(self):
        raise NotImplementedError

    @pytest.fixture
    def mock_search(self):
        raise NotImplementedError

    @pytest.fixture
    def mock_search_failure(self):
        raise NotImplementedError

    @pytest.fixture
    def search_url(self):
        raise NotImplementedError

    @pytest.fixture
    def mock_passage(self):
        raise NotImplementedError

    @pytest.fixture
    def mock_passage_failure(self):
        raise NotImplementedError

    @pytest.fixture
    def bible(self):
        return Bible(command='bib',
                     name='The Bible',
                     abbr='BIB',
                     service='MyService',
                     service_version='eng-BIB',
                     rtl=False)

    def get_passages_url(self, version: str, verses: VerseRange) -> str:
        raise NotImplementedError

    def test_init(self, service):
        assert service is not None

    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_search')
    async def test_search(self, mocker, mock_client_session, service, bible, search_url):
        response = await service.search(bible, ['one', 'two', 'three'])

        assert mock_client_session.get.call_args[0] == mocker.call(search_url)[1]
        assert response == SearchResults([
            VerseRange.from_string('John 1:1-4'),
            VerseRange.from_string('Genesis 50:1')
        ], 50)

    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_search_failure')
    async def test_search_bad_response(self, mocker, mock_client_session, service, bible):
        with pytest.raises(DoNotUnderstandError):
            await service.search(bible, ['one', 'two', 'three'])

    @pytest.mark.parametrize('verse,expected,mock_passage', [
        (VerseRange.from_string('Gal 3:10-11'),
         Passage(Galatians_3_10_11, VerseRange.from_string('Gal 3:10-11'), 'BIB'),
         'Galatians 3:10-11'),
        (VerseRange.from_string('Mark 5:1'),
         Passage(Mark_5_1, VerseRange.from_string('Mark 5:1'), 'BIB'),
         'Mark 5:1')
    ], indirect=['mock_passage'])
    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_passage')
    async def test_get_passage(self, verse, expected, mocker, mock_client_session,
                               service, bible):
        response = await service.get_passage(bible, verse)
        passages_url = self.get_passages_url(bible['service_version'], verse)
        assert mock_client_session.get.call_args[0] == mocker.call(passages_url)[1]
        assert response == expected

    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_passage_failure')
    async def test_get_passage_no_passages(self, service, bible):
        with pytest.raises(DoNotUnderstandError):
            await service.get_passage(bible, VerseRange.from_string('John 1:2-3'))
