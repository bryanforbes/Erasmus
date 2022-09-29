from __future__ import annotations

from dataclasses import MISSING, Field, dataclass, field as _dataclass_field
from enum import Flag as _EnumFlag
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
from sqlalchemy import BigInteger, Boolean, Column, TypeDecorator
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import (
    Mapped as _SAMapped,
    registry,
    relationship as _sa_relationship,
)

from sqlalchemy.orm import foreign as _sa_foreign  # pyright: ignore  # isort: skip
from sqlalchemy.orm import remote as _sa_remote  # pyright: ignore  # isort: skip

_T = TypeVar('_T')
_FlagT = TypeVar('_FlagT', bound=_EnumFlag)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.sql import ClauseElement
    from sqlalchemy.sql.base import SchemaEventTarget
    from sqlalchemy.sql.elements import ColumnElement
    from sqlalchemy.types import TypeEngine

    _ComparatorBase = TypeEngine.Comparator['TSVector']

    class _TypeDecorator(TypeDecorator[_T]):
        ...

else:
    _ComparatorBase = TSVECTOR.Comparator

    class _TypeDecorator(TypeDecorator, Generic[_T]):
        ...


_mapper_registry: Final = registry()

mapped: Final = _mapper_registry.mapped
Session: Final = async_sessionmaker(expire_on_commit=False)


class TSVector(_TypeDecorator[str]):
    impl = TSVECTOR
    cache_ok = True

    class Comparator(_ComparatorBase):
        def match(self, other: object, **kwargs: object) -> ColumnElement[Boolean]:
            if (
                'postgresql_regconfig' not in kwargs
                and 'regconfig' in self.type.options
            ):
                kwargs['postgresql_regconfig'] = self.type.options['regconfig']
            return TSVECTOR.Comparator.match(self, other, **kwargs)

        def __or__(self, other: object) -> ColumnElement[TSVector]:
            return self.op('||')(other)  # type: ignore

    comparator_factory = Comparator  # type: ignore

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initializes new TSVectorType

        :param *args: list of column names
        :param **kwargs: various other options for this TSVectorType
        """
        self.columns = args
        self.options = kwargs

        super().__init__()


class Flag(_TypeDecorator[_FlagT]):
    impl = BigInteger
    cache_ok = True

    _flag_cls: type[_FlagT]

    def __init__(
        self, flag_cls: type[_FlagT], /, *args: object, **kwargs: object
    ) -> None:
        self._flag_cls = flag_cls
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: _FlagT | None, dialect: object) -> int | None:
        return value.value if value is not None else value

    def process_result_value(self, value: int | None, dialect: object) -> _FlagT | None:
        if value is not None:
            return self._flag_cls(value)  # type: ignore

        return value


@dataclass
class Base:
    __sa_dataclass_metadata_key__ = 'sa'


_BaseT = TypeVar('_BaseT', bound=Base)


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


def remote(expr: _CEA, /) -> _CEA:
    return _sa_remote(expr)  # pyright: ignore


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
