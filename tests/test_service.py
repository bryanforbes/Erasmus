import pytest
from typing import Any
from erasmus.service import Service
from erasmus.data import Passage


@pytest.mark.usefixtures('mock_aiohttp')
class TestService(object):
    @pytest.fixture
    def MyService(self, mocker):
        class MyService(Service[Any]):
            _get_passage_url = mocker.Mock()
            _get_passage_text = mocker.Mock()
            _get_search_url = mocker.Mock()
            _get_search_results = mocker.Mock()
            _process_response = mocker.AsyncMock()

        return MyService

    def test_init(self):
        config = {}

        with pytest.raises(TypeError):
            Service(config)

    @pytest.mark.asyncio
    async def test_get_passage(self, MyService, mock_response, mock_client_session):
        service = MyService({})
        passage = Passage.from_string('Leviticus 1:2-3')

        service._get_passage_url.return_value = 'http://example.com'
        service._process_response.return_value = 'foo bar baz'
        service._get_passage_text.return_value = 'passage result'

        result = await service.get_passage('version', passage)

        service._get_passage_url.assert_called_once_with('version', passage)
        mock_client_session.get.assert_called_once_with('http://example.com')
        service._process_response.assert_called_once_with(mock_response)
        service._get_passage_text.assert_called_once_with('foo bar baz')
        assert result == 'passage result'

    @pytest.mark.asyncio
    async def test_search(self, MyService, mock_response, mock_client_session):
        service = MyService({})

        service._get_search_url.return_value = 'http://example.com'
        service._process_response.return_value = 'foo bar baz'
        service._get_search_results.return_value = 'search result'

        result = await service.search('version', ['one', 'two', 'three'])

        service._get_search_url.assert_called_once_with('version', ['one', 'two', 'three'])
        mock_client_session.get.assert_called_once_with('http://example.com')
        service._process_response.assert_called_once_with(mock_response)
        service._get_search_results.assert_called_once_with('foo bar baz')

        assert result == 'search result'
