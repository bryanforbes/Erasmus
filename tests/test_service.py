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
    async def test_get(self):
        service = Service({})

        with pytest.raises(NotImplementedError):
            await service.get('/foo/bar/baz')
