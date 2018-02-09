from typing import Iterable, Iterator, Set, TypeVar, Optional, Callable, Any
from itertools import filterfalse

_T = TypeVar('_T')


def unique_seen(iterable: Iterable[_T], get_key: Optional[Callable[[_T], Any]] = None) -> Iterator[_T]:
    seen: Set[Any] = set()
    if get_key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen.add(element)
            yield element
    else:
        for element in iterable:
            key = get_key(element)
            if key not in seen:
                seen.add(key)
                yield element
