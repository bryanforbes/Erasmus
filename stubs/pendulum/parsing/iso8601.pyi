from datetime import date, datetime, time
from re import Pattern

ISO8601_DT: Pattern[str]
ISO8601_DURATION: Pattern[str]

def parse_iso8601(text: str) -> time | date | datetime | None: ...
