from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar, Generic, Literal, TypeAlias, TypeVar, overload
from typing_extensions import Self

import attr
from babel.numbers import NumberPattern

_T = TypeVar('_T')
_FluentNumberT = TypeVar('_FluentNumberT', bound=FluentNumber[Any])
_FluentDateTypeT = TypeVar('_FluentDateTypeT', bound=FluentDateType)

_FormatStyleOptions: TypeAlias = Literal['decimal', 'currency', 'percent']
_CurrencyDisplayOptions: TypeAlias = Literal['symbol', 'code', 'name']
_DateTimeStyleOptions: TypeAlias = Literal['full', 'long', 'medium', 'short']

FORMAT_STYLE_DECIMAL: Literal['decimal'] = ...
FORMAT_STYLE_CURRENCY: Literal['currency'] = ...
FORMAT_STYLE_PERCENT: Literal['percent'] = ...
FORMAT_STYLE_OPTIONS: set[_FormatStyleOptions] = ...
CURRENCY_DISPLAY_SYMBOL: Literal['symbol'] = ...
CURRENCY_DISPLAY_CODE: Literal['code'] = ...
CURRENCY_DISPLAY_NAME: Literal['name'] = ...
CURRENCY_DISPLAY_OPTIONS: set[_CurrencyDisplayOptions] = ...
DATE_STYLE_OPTIONS: set[_DateTimeStyleOptions | None] = ...
TIME_STYLE_OPTIONS: set[_DateTimeStyleOptions | None] = ...

class FluentType:
    def format(self, locale: str) -> str: ...

class FluentNone(FluentType):
    name: str
    def __init__(self, name: str = ...) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def format(self, locale: str) -> str: ...

@attr.s
class NumberFormatOptions:
    style: _FormatStyleOptions = ...
    currency: str | None = ...
    currencyDisplay: _CurrencyDisplayOptions = ...
    useGrouping: bool = ...
    minimumIntegerDigits: int | None = ...
    minimumFractionDigits: int | None = ...
    maximumFractionDigits: int | None = ...
    minimumSignificantDigits: int | None = ...
    maximumSignificantDigits: int | None = ...

class FluentNumber(FluentType, Generic[_T]):
    default_number_format_options: ClassVar[NumberFormatOptions]
    value: _T
    options: NumberFormatOptions
    def __new__(cls, value: float, **kwargs: Any) -> Self: ...
    def format(self, locale: str) -> str: ...

def merge_options(
    options_class: type[_T],
    base: _T,
    kwargs: Mapping[str, Any],
) -> _T: ...

class FluentInt(FluentNumber[int], int): ...
class FluentFloat(FluentNumber[float], float): ...
class FluentDecimal(FluentNumber[Decimal], Decimal): ...

@overload
def fluent_number(number: _FluentNumberT) -> _FluentNumberT: ...  # type: ignore
@overload
def fluent_number(number: int, **kwargs: Any) -> FluentInt: ...  # type: ignore
@overload
def fluent_number(number: float, **kwargs: Any) -> FluentFloat: ...
@overload
def fluent_number(number: Decimal, **kwargs: Any) -> FluentDecimal: ...
@overload
def fluent_number(number: FluentNone, **kwargs: Any) -> FluentNone: ...
@overload
def fluent_number(
    number: Any, **kwargs: Any
) -> FluentInt | FluentFloat | FluentDecimal | FluentNone: ...
def clone_pattern(pattern: NumberPattern) -> NumberPattern: ...
@attr.s
class DateFormatOptions:
    timeZone: Any = ...
    hour12: Any = ...
    weekday: Any = ...
    era: Any = ...
    year: Any = ...
    month: Any = ...
    day: Any = ...
    hour: Any = ...
    minute: Any = ...
    second: Any = ...
    timeZoneName: Any = ...
    dateStyle: _DateTimeStyleOptions | None = ...
    timeStyle: _DateTimeStyleOptions | None = ...

class FluentDateType(FluentType):
    options: DateFormatOptions
    def format(self, locale: str) -> str: ...

class FluentDate(FluentDateType, date):
    @classmethod
    def from_date(cls, dt_obj: date, **kwargs: Any) -> Self: ...

class FluentDateTime(FluentDateType, datetime):
    @classmethod
    def from_date_time(cls, dt_obj: datetime, **kwargs: Any) -> Self: ...

@overload
def fluent_date(dt: _FluentDateTypeT) -> _FluentDateTypeT: ...  # type: ignore
@overload
def fluent_date(dt: datetime, **kwargs: Any) -> FluentDateTime: ...  # type: ignore
@overload
def fluent_date(dt: date, **kwargs: Any) -> FluentDate: ...
@overload
def fluent_date(dt: FluentNone, **kwargs: Any) -> FluentNone: ...
@overload
def fluent_date(dt: Any, **kwargs: Any) -> FluentDateTime | FluentDate | FluentNone: ...
