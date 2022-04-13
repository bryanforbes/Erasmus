from __future__ import annotations

from typing import Any

import pytest

from erasmus.json import get, has


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
def test_get(data: dict[str, Any], key: str, expected: Any) -> None:
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
def test_jsonobject_has(data: dict[str, Any], key: str, expected: Any) -> None:
    assert has(data, key) == expected
