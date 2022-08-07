from datetime import date, datetime
from typing import NamedTuple

class PreciseDiff(NamedTuple):
    years: int
    months: int
    days: int
    hours: int
    minutes: int
    seconds: int
    microseconds: int

def is_leap(year: int) -> bool: ...
def is_long_year(year: int) -> bool: ...
def week_day(year: int, month: int, day: int) -> int: ...
def days_in_year(year: int) -> int: ...
def timestamp(dt: datetime) -> int: ...
def local_time(
    unix_time: int, utc_offset: int, microseconds: int
) -> tuple[int, int, int, int, int, int, int]: ...
def precise_diff(
    d1: datetime | date,
    d2: datetime | date,
) -> PreciseDiff: ...
