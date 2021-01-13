from __future__ import annotations

from typing import Any, Dict

import pytest
import pytest_mock

from erasmus.json import get, has, load, loads


def test_load(mocker: pytest_mock.MockFixture) -> None:
    mock = mocker.mock_open(read_data='{ "foo": { "bar": "baz" }, "spam": "ham" }')

    with mock() as fp:
        result = load(fp)

    assert result == {'foo': {'bar': 'baz'}, 'spam': 'ham'}


def test_loads() -> None:
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
def test_get(data: Dict[str, Any], key: str, expected: Any) -> None:
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
def test_jsonobject_has(data: Dict[str, Any], key: str, expected: Any) -> None:
    assert has(data, key) == expected
