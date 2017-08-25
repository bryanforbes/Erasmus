import pytest
from erasmus.services import Service

def test_init():
    config = {}
    service = Service(config)
    assert service.config is config

@pytest.mark.asyncio
async def test_get_verse():
    service = Service({})

    with pytest.raises(NotImplementedError):
        await service.get_verse('', '', 1, 1)

@pytest.mark.asyncio
async def test__get_url():
    service = Service({})

    with pytest.raises(NotImplementedError):
        await service._get_url('/foo/bar/baz')
