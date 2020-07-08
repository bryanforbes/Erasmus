from typing import Any

import pytest
from attr import attrib, dataclass

from erasmus.data import VerseRange
from erasmus.services.base_service import BaseService


@pytest.mark.usefixtures('mock_aiohttp')
class TestService(object):
    @pytest.fixture
    def MyService(self, mocker):
        @dataclass(slots=True)
        class MyService(BaseService):
            _request_passage: Any = attrib(factory=mocker.Mock)
            _request_search: Any = attrib(factory=mocker.Mock)

        return MyService

    @pytest.fixture
    def bible(self, MockBible):
        return MockBible(
            command='bib',
            name='The Bible',
            abbr='BIB',
            service='MyService',
            service_version='eng-BIB',
            rtl=False,
        )

    def test_init(self):
        config = {}

        with pytest.raises(TypeError):
            BaseService(config)

    @pytest.mark.asyncio
    async def test_get_passage(
        self, mocker, MyService, bible, mock_response, mock_client_session
    ):
        expected = mocker.MagicMock()
        passage = mocker.MagicMock()
        passage.__aenter__.return_value = expected

        service = MyService(config={}, session=mock_client_session)
        service._request_passage.return_value = passage
        verses = VerseRange.from_string('Leviticus 1:2-3')

        result = await service.get_passage(bible, verses)

        assert result is expected

    @pytest.mark.asyncio
    async def test_search(
        self, mocker, MyService, bible, mock_response, mock_client_session
    ):
        expected = mocker.sentinel.SEARCH_RESULTS
        search_results = mocker.MagicMock()
        search_results.__aenter__.return_value = expected

        service = MyService(config={}, session=mock_client_session)
        service._request_search.return_value = search_results

        result = await service.search(
            bible, ['one', 'two', 'three'], limit=10, offset=20
        )

        assert result is expected
