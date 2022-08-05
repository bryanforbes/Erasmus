from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeVar, overload

from ..syntax.ast import MessageReference, TermReference
from .errors import FluentReferenceError
from .types import FluentDate, FluentDateTime, FluentDecimal, FluentFloat, FluentInt

_T = TypeVar('_T')

TERM_SIGIL: Literal['-'] = ...
ATTRIBUTE_SEPARATOR: Literal['.'] = ...

@overload
def native_to_fluent(val: int) -> FluentInt: ...  # type: ignore
@overload
def native_to_fluent(val: float) -> FluentFloat: ...
@overload
def native_to_fluent(val: Decimal) -> FluentDecimal: ...
@overload
def native_to_fluent(val: datetime) -> FluentDateTime: ...  # type: ignore
@overload
def native_to_fluent(val: date) -> FluentDate: ...
@overload
def native_to_fluent(val: _T) -> _T: ...
def reference_to_id(ref: TermReference | MessageReference) -> str: ...
def unknown_reference_error_obj(ref_id: str) -> FluentReferenceError: ...
