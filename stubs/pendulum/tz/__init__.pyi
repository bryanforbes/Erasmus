from typing import Final, Literal, overload

from .local_timezone import (
    get_local_timezone as get_local_timezone,
    set_local_timezone as set_local_timezone,
    test_local_timezone as test_local_timezone,
)
from .timezone import UTC as UTC, FixedTimezone as _FixedTimezone, Timezone as _Timezone

PRE_TRANSITION: Final[Literal['pre']]
POST_TRANSITION: Final[Literal['post']]
TRANSITION_ERROR: Final[Literal['error']]
timezones: Final[tuple[str, ...]]

@overload
def timezone(name: int, extended: bool = ...) -> _FixedTimezone: ...
@overload
def timezone(name: str, extended: bool = ...) -> _Timezone: ...
def fixed_timezone(offset: int) -> _FixedTimezone: ...
def local_timezone() -> _Timezone: ...
