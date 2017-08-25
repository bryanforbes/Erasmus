import pytest
from erasmus.service import Service, Passage

def test_passage():
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

def test_init():
    config = {}
    service = Service(config)
    assert service.config is config

@pytest.mark.asyncio
async def test_get_passage(mocker):
    service = Service({})
    passage = Passage('book', 1, 2, 3)

    mocker.patch.object(service, '_parse_passage', return_value='John 1:1-4')
    mocker.spy(service, '_get_passage')

    with pytest.raises(NotImplementedError):
        await service.get_passage('version', passage)

    assert service._parse_passage.call_count == 1
    assert service._parse_passage.call_args == mocker.call(passage)
    assert service._get_passage.call_count == 1
    assert service._get_passage.call_args == mocker.call('version', 'John 1:1-4')

def test__parse_passage():
    service = Service({})
    passage = Passage('book', 1, 2, 3)

    with pytest.raises(NotImplementedError):
        service._parse_passage(passage)

@pytest.mark.asyncio
async def test__get_passage():
    service = Service({})

    with pytest.raises(NotImplementedError):
        await service._get_passage('version', 'passage')

@pytest.mark.asyncio
async def test__get_url():
    service = Service({})

    with pytest.raises(NotImplementedError):
        await service._get_url('/foo/bar/baz')
