import pytest
from erasmus.json import load, loads, get, has


def test_load(mocker):
    mock = mocker.mock_open(read_data='{ "foo": { "bar": "baz" }, "spam": "ham" }')

    with mock() as fp:
        result = load(fp)

    assert result == {'foo': {'bar': 'baz'}, 'spam': 'ham'}


def test_loads():
    result = loads('{ "foo": { "bar": "baz" }, "spam": "ham" }')

    assert result == {'foo': {'bar': 'baz'}, 'spam': 'ham'}


@pytest.mark.parametrize(
    'data,key,expected',
    [
        ({'foo': {'bar': {'baz': 1}}}, 'foo.bar.baz', 1),
        ({'foo': [{'bar': 1}]}, 'foo.0.bar', 1),
        ({'foo': [{'bar': 1}]}, 'foo.0.baz', None),
        ({}, 'foo', None),
        ({'foo': 1}, 'foo.bar.baz', None),
    ],
)
def test_get(data, key, expected):
    assert get(data, key) == expected


@pytest.mark.parametrize(
    'data,key,expected',
    [
        ({'foo': {'bar': {'baz': 1}}}, 'foo.bar.baz', True),
        ({'foo': [{'bar': 1}]}, 'foo.0.bar', True),
        ({'foo': [{'bar': 1}]}, 'foo.0.baz', False),
        ({}, 'foo', False),
        ({'foo': 1}, 'foo.bar.baz', False),
    ],
)
def test_jsonobject_has(data, key, expected):
    assert has(data, key) == expected
