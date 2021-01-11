import aiohttp
import pytest

from erasmus.data import SearchResults, VerseRange
from erasmus.exceptions import DoNotUnderstandError

Galatians_3_10_11 = (
    '**10.** For as many as are of the works of the Law are under a '
    'curse; for it is written, “CURSED IS EVERYONE WHO DOES NOT '
    'ABIDE BY ALL THINGS WRITTEN IN THE BOOK OF THE LAW, TO '
    'PERFORM THEM.” **11.** Now that no one is justified by the Law '
    'before God is evident; for, “THE RIGHTEOUS MAN SHALL LIVE BY '
    'FAITH.”'
)

Mark_5_1 = (
    '**1.** They came to the other side of the sea, into the country of the Gerasenes.'
)


class ServiceTest(object):
    @pytest.fixture
    async def session(self, event_loop):
        async with aiohttp.ClientSession(loop=event_loop) as session:
            yield session

    @pytest.fixture
    def bible(self, request, default_version, default_abbr, MockBible):
        name = request.function.__name__

        if name == 'test_search':
            data = request.getfixturevalue('search_data')
        elif name == 'test_get_passage':
            data = request.getfixturevalue('passage_data')
        else:
            data = {}

        return MockBible(
            command='bib',
            name='The Bible',
            abbr=data.get('abbr', default_abbr),
            service='MyService',
            service_version=data.get('version', default_version),
            rtl=False,
        )

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_search(self, session, search_data, service, bible):
        response = await service.search(session, bible, search_data['terms'])
        assert response == SearchResults(search_data['verses'], search_data['total'])

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_get_passage(self, session, passage_data, service, bible):
        response = await service.get_passage(session, bible, passage_data['verse'])
        assert response == passage_data['passage']

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_get_passage_no_passages(self, session, service, bible):
        with pytest.raises(DoNotUnderstandError):
            await service.get_passage(
                session, bible, VerseRange.from_string('John 50:1-4')
            )
