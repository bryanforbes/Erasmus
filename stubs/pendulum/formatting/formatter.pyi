from typing import Any, TypedDict

from ..datetime import DateTime
from ..locales.locale import Locale

class _Parsed(TypedDict):
    year: Any
    month: Any
    day: Any
    hour: Any
    minute: Any
    second: Any
    microsecond: Any
    tz: Any
    quarter: Any
    day_of_week: Any
    day_of_year: Any
    meridiem: Any
    timestamp: Any

class Formatter:
    def format(
        self,
        dt: DateTime,
        fmt: str,
        locale: str | Locale | None = ...,
    ) -> str: ...
    def parse(
        self,
        time: str,
        fmt: str,
        now: DateTime,
        locale: str | None = ...,
    ) -> _Parsed: ...
