from __future__ import absolute_import

import datetime as _datetime

from .__version__ import __version__ as __version__
from .constants import (
    DAYS_PER_WEEK as DAYS_PER_WEEK,
    FRIDAY as FRIDAY,
    HOURS_PER_DAY as HOURS_PER_DAY,
    MINUTES_PER_HOUR as MINUTES_PER_DAY,
    MONDAY as MONDAY,
    MONTHS_PER_YEAR as MONTHS_PER_YEAR,
    SATURDAY as SATURDAY,
    SECONDS_PER_DAY as SECONDS_PER_DAY,
    SECONDS_PER_HOUR as SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE as SECONDS_PER_MINUTE,
    SUNDAY as SUNDAY,
    THURSDAY as THURSDAY,
    TUESDAY as TUESDAY,
    WEDNESDAY as WEDNESDAY,
    WEEKS_PER_YEAR as WEEKS_PER_YEAR,
    YEARS_PER_CENTURY as YEARS_PER_CENTURY,
    YEARS_PER_DECADE as YEARS_PER_DECADE,
)
from .date import Date as Date
from .datetime import DateTime as DateTime
from .duration import Duration as Duration
from .formatting import Formatter as Formatter
from .helpers import (
    format_diff as format_diff,
    get_locale as get_locale,
    get_test_now as get_test_now,
    has_test_now as has_test_now,
    locale as locale,
    set_locale as set_locale,
    set_test_now as set_test_now,
    test as test,
    week_ends_at as week_ends_at,
    week_starts_at as week_starts_at,
)
from .parser import parse as parse
from .period import Period as Period
from .time import Time as Time
from .tz import (
    POST_TRANSITION,
    PRE_TRANSITION,
    TRANSITION_ERROR,
    UTC,
    local_timezone,
    set_local_timezone,
    test_local_timezone,
    timezone,
    timezones,
)
from .tz.timezone import Timezone as _Timezone

def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = ...,
    minute: int = ...,
    second: int = ...,
    microsecond: int = ...,
    tz: str | float | _Timezone | None = ...,
    dst_rule: str = ...,
) -> DateTime: ...
def local(
    year: int,
    month: int,
    day: int,
    hour: int = ...,
    minute: int = ...,
    second: int = ...,
    microsecond: int = ...,
) -> DateTime: ...
def naive(
    year: int,
    month: int,
    day: int,
    hour: int = ...,
    minute: int = ...,
    second: int = ...,
    microsecond: int = ...,
) -> DateTime: ...
def date(year: int, month: int, day: int) -> Date: ...
def time(
    hour: int, minute: int = ..., second: int = ..., microsecond: int = ...
) -> Time: ...
def instance(dt: _datetime.datetime, tz: str | _Timezone | None = ...) -> DateTime: ...
def now(tz: str | _Timezone | None = ...) -> DateTime: ...
def today(tz: str | _Timezone = ...) -> DateTime: ...
def tomorrow(tz: str | _Timezone = ...) -> DateTime: ...
def yesterday(tz: str | _Timezone = ...) -> DateTime: ...
def from_format(
    string: str, fmt: str, tz: str | _Timezone = ..., locale: str | None = ...
) -> DateTime: ...
def from_timestamp(timestamp: float, tz: str | _Timezone = ...) -> DateTime: ...
def duration(
    days: float = ...,
    seconds: float = ...,
    microseconds: float = ...,
    milliseconds: float = ...,
    minutes: float = ...,
    hours: float = ...,
    weeks: float = ...,
    years: float = ...,
    months: float = ...,
) -> Duration: ...
def period(start: DateTime, end: DateTime, absolute: bool = ...) -> Period: ...
