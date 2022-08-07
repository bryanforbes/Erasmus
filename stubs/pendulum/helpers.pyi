from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from typing import TypeVar, overload

from ._extensions.helpers import (
    days_in_year as days_in_year,
    is_leap as is_leap,
    is_long_year as is_long_year,
    local_time as local_time,
    precise_diff as precise_diff,
    timestamp as timestamp,
    week_day as week_day,
)
from .datetime import DateTime
from .locales.locale import Locale
from .period import Period

_DT = TypeVar("_DT", bound=datetime)
_D = TypeVar("_D", bound=date)

@overload
def add_duration(
    dt: _DT,
    years: int = ...,
    months: int = ...,
    weeks: int = ...,
    days: int = ...,
    hours: int = ...,
    minutes: int = ...,
    seconds: int = ...,
    microseconds: int = ...,
) -> _DT: ...
@overload
def add_duration(
    dt: _D, years: int = ..., months: int = ..., weeks: int = ..., days: int = ...
) -> _D: ...
def format_diff(
    diff: Period, is_now: bool = ..., absolute: bool = ..., locale: str | None = ...
) -> str: ...
@contextmanager
def test(mock: DateTime) -> Iterator[None]: ...
def set_test_now(test_now: DateTime | None = ...) -> None: ...
def get_test_now() -> DateTime | None: ...
def has_test_now() -> bool: ...
def locale(name: str) -> Locale: ...
def set_locale(name: str) -> None: ...
def get_locale() -> str: ...
def week_starts_at(wday: int) -> None: ...
def week_ends_at(wday: int) -> None: ...
