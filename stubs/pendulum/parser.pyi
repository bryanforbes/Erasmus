from typing import Any

from .date import Date
from .datetime import DateTime
from .duration import Duration
from .time import Time

def parse(text: str, **options: Any) -> Date | Time | DateTime | Duration: ...
