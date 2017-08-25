import pytest
from erasmus.config import load, ConfigObject

def test_load(mocker):
    mock = mocker.mock_open(read_data='{ "foo": { "bar": "baz" }, "spam": "ham" }')

    mocker.patch('erasmus.config.open', mock)

    result = load('some/file.json')

    assert type(result) is ConfigObject
    assert hasattr(result, 'foo')
    assert result.foo == { 'bar': 'baz' }
    assert result.spam == 'ham'
