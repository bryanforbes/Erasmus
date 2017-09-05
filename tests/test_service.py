import pytest
from erasmus.service import Service
from erasmus.data import Passage


@pytest.mark.usefixtures('mock_aiohttp')
class TestService(object):
    def test_init(self):
        config = {}
        service = Service(config)
        assert service.config is config

    @pytest.mark.asyncio
    async def test_get_passage(self, mocker):
        service = Service({})
        passage = Passage.from_string('book 1:2-3')

        with pytest.raises(NotImplementedError):
            await service.get_passage('version', passage)

    @pytest.mark.asyncio
    async def test_search(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service.search('version', ['one', 'two', 'three'])

    @pytest.mark.asyncio
    async def test__get(self, mock_response, mock_client_session):
        service = Service({})

        async with await service._get('/foo/bar/baz') as session:
            assert session is mock_response
            mock_client_session.get.wrap_assert_called_once_with('/foo/bar/baz')

    @pytest.mark.asyncio
    async def test_get(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service.get('/foo/bar/baz')
