from __future__ import annotations

from dataclasses import MISSING, Field, dataclass, field as _dataclass_field
from typing import TYPE_CHECKING, Any, Final, Literal, TypeVar, cast, overload
from typing_extensions import dataclass_transform

from botus_receptus.sqlalchemy import async_sessionmaker
from sqlalchemy import Column as _SAColumn, TypeDecorator
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import (
    Mapped as _SAMapped,
    registry,
    relationship as _sa_relationship,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.sql.base import SchemaEventTarget
    from sqlalchemy.sql.elements import ColumnElement
    from sqlalchemy.types import TypeEngine

    _TSVectorBase = TypeDecorator[str]
    _ComparatorBase = TypeEngine.Comparator['TSVector']
else:
    _TSVectorBase = TypeDecorator
    _ComparatorBase = TSVECTOR.Comparator


_mapper_registry: Final = registry()

mapped: Final = _mapper_registry.mapped
Session: Final = async_sessionmaker(expire_on_commit=False)


class TSVector(_TSVectorBase):
    impl = TSVECTOR
    cache_ok = True

    class Comparator(_ComparatorBase):  # type: ignore
        def match(self, other: Any, **kwargs: Any) -> Any:
            if (
                'postgresql_regconfig' not in kwargs
                and 'regconfig' in self.type.options
            ):
                kwargs['postgresql_regconfig'] = self.type.options['regconfig']
            return TSVECTOR.Comparator.match(self, other, **kwargs)  # type: ignore

        def __or__(self, other: Any) -> ColumnElement[TSVector]:
            return self.op('||')(other)  # type: ignore

    comparator_factory = Comparator  # type: ignore

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes new TSVectorType

        :param *args: list of column names
        :param **kwargs: various other options for this TSVectorType
        """
        self.columns = args
        self.options = kwargs

        super().__init__()


@dataclass
class Base:
    __sa_dataclass_metadata_key__ = 'sa'


_BaseT = TypeVar('_BaseT', bound=Base)
_T = TypeVar('_T')


class Mapped(_SAMapped[_T]):
    def __set__(self, instance: object, value: _T) -> Any:
        raise NotImplementedError()


@overload
def Column(
    column_type: TypeEngine[_T] | type[TypeEngine[_T]],
    /,
    *args: SchemaEventTarget,
    primary_key: Literal[True],
    init: Literal[False] = False,
) -> Mapped[_T]:
    ...


@overload
def Column(
    column_type: TypeEngine[_T] | type[TypeEngine[_T]],
    /,
    *args: SchemaEventTarget,
    primary_key: Literal[True],
    init: Literal[True],
) -> Mapped[_T]:
    ...


@overload
def Column(
    column_type: TypeEngine[_T] | type[TypeEngine[_T]],
    /,
    *args: SchemaEventTarget,
    nullable: Literal[False],
    unique: bool | None = ...,
    init: bool = True,
) -> Mapped[_T]:
    ...


@overload
def Column(
    column_type: TypeEngine[_T] | type[TypeEngine[_T]],
    /,
    *args: SchemaEventTarget,
    primary_key: Literal[False] = ...,
    nullable: Literal[True] = ...,
    unique: bool | None = ...,
    init: bool = True,
) -> Mapped[_T | None]:
    ...


def Column(*args: Any, init: Any = MISSING, **kwargs: Any) -> Any:
    if init is MISSING:
        primary_key = kwargs.get('primary_key', False)
        init = not primary_key

    metadata = {'sa': _SAColumn(*args, **kwargs)}

    return _dataclass_field(init=init, metadata=metadata)


def mixin_column(
    initializer: Callable[[], Mapped[_T]], /, *, init: bool = True
) -> Mapped[_T]:
    return _dataclass_field(
        init=init,
        metadata={'sa': lambda: cast('Field[_T]', initializer()).metadata['sa']},
    )


@overload
def relationship(
    entity: type[_T],
    /,
    *,
    lazy: str = ...,
    primaryjoin: str = ...,
    uselist: Literal[True] = ...,
    init: Literal[False] = False,
) -> Mapped[list[_T]]:
    ...


@overload
def relationship(
    entity: type[_T],
    /,
    *,
    lazy: str = ...,
    primaryjoin: str = ...,
    uselist: Literal[False],
    nullable: Literal[True] = ...,
    init: Literal[False] = False,
) -> Mapped[_T | None]:
    ...


@overload
def relationship(
    entity: type[_T],
    /,
    *,
    lazy: str = ...,
    primaryjoin: str = ...,
    uselist: Literal[False],
    nullable: Literal[False],
    init: Literal[False] = False,
) -> Mapped[_T]:
    ...


def relationship(
    *args: Any, nullable: Any = None, init: Any = None, **kwargs: Any
) -> Any:
    return _dataclass_field(
        init=False,
        metadata={'sa': lambda: _sa_relationship(*args, **kwargs)},  # pyright: ignore
    )


@dataclass_transform(field_specifiers=(_dataclass_field, mixin_column, relationship))
def model_mixin(cls: type[_BaseT], /) -> type[_BaseT]:
    return dataclass(cls)


@dataclass_transform(field_specifiers=(_dataclass_field, Column, relationship))
def model(cls: type[_BaseT], /) -> type[_BaseT]:
    return mapped(dataclass(cls))
