import pytest
from erasmus.json import JSONObject, load, loads


def test_load(mocker):
    mock = mocker.mock_open(read_data='{ "foo": { "bar": "baz" }, "spam": "ham" }')

    with mock() as fp:
        result = load(fp)

    assert type(result) is JSONObject
    assert result.get('foo.bar') == 'baz'
    assert result.get('spam') == 'ham'


def test_loads():
    result = loads('{ "foo": { "bar": "baz" }, "spam": "ham" }')

    assert type(result) is JSONObject
    assert result.get('foo.bar') == 'baz'
    assert result.get('spam') == 'ham'


@pytest.mark.parametrize('data,key,expected', [
    ({'foo': {'bar': {'baz': 1}}}, 'foo.bar.baz', 1),
    ({'foo': [{'bar': 1}]}, 'foo.0.bar', 1),
    ({'foo': [{'bar': 1}]}, 'foo.0.baz', None),
    ({}, 'foo', None),
    ({'foo': 1}, 'foo.bar.baz', None)
])
def test_jsonobject_get(data, key, expected):
    obj = JSONObject(data)
    assert obj.get(key) == expected


@pytest.mark.parametrize('data,key,expected', [
    ({'foo': {'bar': {'baz': 1}}}, 'foo.bar.baz', True),
    ({'foo': [{'bar': 1}]}, 'foo.0.bar', True),
    ({'foo': [{'bar': 1}]}, 'foo.0.baz', False),
    ({}, 'foo', False),
    ({'foo': 1}, 'foo.bar.baz', False)
])
def test_jsonobject_has(data, key, expected):
    obj = JSONObject(data)
    assert obj.has(key) == expected
