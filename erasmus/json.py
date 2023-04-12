from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import orjson

if TYPE_CHECKING:
    from collections.abc import Mapping


def get(
    obj: Mapping[str, object], key: str, fallback: object = None, /
) -> Any:  # noqa: ANN401
    result: Any = obj

    for part in key.split('.'):
        try:
            if isinstance(result, list):
                result = result[int(part)]
            elif isinstance(result, dict):
                result = result[part]
            else:
                return fallback
        except (KeyError, TypeError, IndexError):
            return fallback

    return result


MISSING: Final = object()


def has(obj: Mapping[str, object], key: str, /) -> bool:
    result = get(obj, key, MISSING)

    return result is not MISSING


def serialize(obj: object) -> str:
    return orjson.dumps(obj).decode('utf-8')


def deserialize(json: str) -> object:
    return orjson.loads(json)
