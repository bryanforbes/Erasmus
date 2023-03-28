from datetime import date, datetime, time
from re import Pattern
from typing import Any, Final

from .exceptions import ParserError as ParserError
from .iso8601 import parse_iso8601 as parse_iso8601

COMMON: Final[Pattern[str]]
DEFAULT_OPTIONS: Final[dict[str, Any]]

def parse(
    text: str,
    *,
    day_first: bool = ...,
    year_first: bool = ...,
    strict: bool = ...,
    exact: bool = ...,
    now: date | None = ...,
) -> datetime | _Interval: ...

class _Interval:
    start: date | datetime | time | None
    end: date | datetime | time | None
    duration: date | datetime | time | None
