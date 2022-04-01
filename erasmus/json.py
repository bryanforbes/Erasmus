from __future__ import annotations

from typing import IO, Any, AnyStr

import ujson


def get(obj: Any, key: str, fallback: Any = None, /) -> Any:
    result: Any = obj
    for part in key.split('.'):
        try:
            if isinstance(result, list):
                result: Any = result[int(part)]
            elif isinstance(result, dict):
                result: Any = result[part]
            else:
                return fallback
        except (KeyError, TypeError, IndexError):
            return fallback

    return result


def has(obj: Any, key: str, /) -> bool:
    fallback = object()
    result = get(obj, key, fallback)

    return result is not fallback


def loads(s: AnyStr, /, *args: Any, **kwargs: Any) -> Any:
    return ujson.loads(s, *args, **kwargs)


def load(fp: IO[str], /, *args: Any, **kwargs: Any) -> Any:
    return ujson.load(fp, *args, **kwargs)
