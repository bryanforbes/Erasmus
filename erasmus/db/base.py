from __future__ import annotations

from dataclasses import MISSING, Field, dataclass, field as _dataclass_field
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    Literal,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)
from typing_extensions import Self, dataclass_transform

from botus_receptus.sqlalchemy import async_sessionmaker
from sqlalchemy import Column
from sqlalchemy.ext.hybrid import ExprComparator, hybrid_property as _hybrid_property
from sqlalchemy.orm import (
    Mapped as _SAMapped,
    registry,
    relationship as _sa_relationship,
)

from sqlalchemy.orm import foreign as _sa_foreign  # pyright: ignore  # isort: skip

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.sql import ClauseElement
    from sqlalchemy.sql.base import SchemaEventTarget
    from sqlalchemy.sql.elements import ColumnElement
    from sqlalchemy.types import TypeEngine


_T = TypeVar('_T')
_BaseT = TypeVar('_BaseT', bound="Base")

_mapper_registry: Final = registry()
mapped: Final = _mapper_registry.mapped
Session: Final = async_sessionmaker(expire_on_commit=False)


@dataclass
class Base:
    __sa_dataclass_metadata_key__ = 'sa'


class Mapped(_SAMapped[_T]):
    if TYPE_CHECKING:

        @overload
        def __get__(self, instance: None, owner: type[object] | None = ...) -> Self:
            ...

        @overload
        def __get__(self, instance: object, owner: type[object] | None = ...) -> _T:
            ...

        def __get__(self, instance: Any, owner: Any = None) -> Any:
            ...

        def __set__(self, instance: object, value: _T | ClauseElement) -> None:
            ...

        def __delete__(self, instance: object) -> None:
            ...

        @classmethod
        def _empty_constructor(cls, arg1: object) -> Mapped[_T]:
            ...


_TypeEngineArgument: TypeAlias = 'TypeEngine[_T] | type[TypeEngine[_T]]'


@overload
def mapped_column(
    column_type: _TypeEngineArgument[_T],
    /,
    *args: SchemaEventTarget,
    name: str = ...,
    primary_key: Literal[True],
    init: Literal[False] = False,
    **kwargs: object,
) -> Mapped[Any]:
    ...


@overload
def mapped_column(
    column_type: _TypeEngineArgument[_T],
    /,
    *args: SchemaEventTarget,
    name: str = ...,
    primary_key: Literal[True],
    init: Literal[True],
    **kwargs: object,
) -> Mapped[Any]:
    ...


@overload
def mapped_column(
    column_type: _TypeEngineArgument[_T],
    /,
    *args: SchemaEventTarget,
    name: str = ...,
    primary_key: Literal[False] = ...,
    nullable: bool = ...,
    unique: bool | None = ...,
    init: bool = True,
    **kwargs: object,
) -> Mapped[Any]:
    ...


def mapped_column(*args: Any, init: Any = MISSING, **kwargs: object) -> Any:
    if init is MISSING:
        primary_key = kwargs.get('primary_key', False)
        init = not primary_key

    metadata = {'sa': Column(*args, **kwargs)}

    return _dataclass_field(init=init, metadata=metadata)


def mixin_column(
    initializer: Callable[[], Mapped[Any]], /, *, init: bool = True
) -> Mapped[Any]:
    return _dataclass_field(
        init=init,
        metadata={'sa': lambda: cast('Field[Any]', initializer()).metadata['sa']},
    )


@overload
def relationship(
    entity: type[_T],
    /,
    secondary: type[object] = ...,
    *,
    init: Literal[False] = False,
    lazy: str = ...,
    primaryjoin: object = ...,
    secondaryjoin: object = ...,
    uselist: Literal[True] = ...,
    order_by: object = ...,
    viewonly: bool = ...,
) -> Mapped[list[_T]]:
    ...


@overload
def relationship(
    entity: type[_T],
    /,
    secondary: type[object] = ...,
    *,
    init: Literal[False] = False,
    lazy: str = ...,
    primaryjoin: object = ...,
    secondaryjoin: object = ...,
    uselist: Literal[False],
    nullable: Literal[True] = ...,
    order_by: object = ...,
    viewonly: bool = ...,
) -> Mapped[_T | None]:
    ...


@overload
def relationship(
    entity: type[_T],
    /,
    secondary: type[object] = ...,
    *,
    init: Literal[False] = False,
    lazy: str = ...,
    primaryjoin: object = ...,
    secondaryjoin: object = ...,
    uselist: Literal[False],
    nullable: Literal[False],
    order_by: object = ...,
    viewonly: bool = ...,
) -> Mapped[_T]:
    ...


def relationship(
    *args: Any, init: Any = None, nullable: bool = ..., **kwargs: Any
) -> Any:
    return _dataclass_field(
        init=False,
        metadata={'sa': lambda: _sa_relationship(*args, **kwargs)},  # pyright: ignore
    )


_CEA = TypeVar('_CEA', bound='ColumnElement[Any] | Callable[[], ColumnElement[Any]]')


def foreign(expr: _CEA, /) -> _CEA:
    return _sa_foreign(expr)  # pyright: ignore


def deref_column(obj: Mapped[_T]) -> Mapped[_T]:
    if isinstance(obj, Field):
        return cast('Field[_T]', obj).metadata['sa']
    return obj


@dataclass_transform(field_specifiers=(_dataclass_field, mixin_column, relationship))
def model_mixin(cls: type[_BaseT], /) -> type[_BaseT]:
    return dataclass(cls)


@dataclass_transform(field_specifiers=(_dataclass_field, mapped_column, relationship))
def model(cls: type[_BaseT], /) -> type[_BaseT]:
    return mapped(dataclass(cls))


if TYPE_CHECKING:

    class hybrid_property(_hybrid_property, Generic[_T]):
        fget: Callable[[Any], _T]

        def __init__(
            self,
            fget: Callable[[Any], _T],
            fset: Any | None = ...,
            fdel: Any | None = ...,
            expr: Any | None = ...,
            custom_comparator: Any | None = ...,
            update_expr: Any | None = ...,
        ) -> None:
            ...

        def getter(self, fget: Callable[[Any], Any]) -> Self:
            ...

        def setter(self, fset: Callable[[Any, _T], None]) -> Self:
            ...

        def deleter(self, fdel: Callable[[Any], None]) -> Self:
            ...

        def expression(self, expr: Callable[[Any], Any]) -> Self:
            ...

        def update_expression(self, meth: Callable[[Any, _T], Any]) -> Self:
            ...

        @overload
        def __get__(
            self, instance: None, owner: type[object] | None = ...
        ) -> ExprComparator:
            ...

        @overload
        def __get__(self, instance: object, owner: type[object] | None = ...) -> _T:
            ...

        def __get__(self, instance: Any, owner: Any = None) -> Any:
            ...

else:
    hybrid_property = _hybrid_property
