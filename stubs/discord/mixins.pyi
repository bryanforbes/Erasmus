from typing import Any, Hashable as TypingHashable


class EqualityComparable:
    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...


class Hashable(EqualityComparable, TypingHashable):
    ...
