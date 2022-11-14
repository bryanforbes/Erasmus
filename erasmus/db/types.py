from __future__ import annotations

from enum import Flag as _EnumFlag
from typing import TYPE_CHECKING, Generic, TypeVar

import pendulum
from pendulum.tz.timezone import Timezone as _Timezone
from sqlalchemy import BigInteger, Boolean, String, TypeDecorator
from sqlalchemy.dialects.postgresql import TIME, TIMESTAMP, TSVECTOR
from sqlalchemy.types import TypeEngine

if TYPE_CHECKING:
    from datetime import datetime, time

    from sqlalchemy.sql.elements import ColumnElement


_T = TypeVar('_T')
_FlagT = TypeVar('_FlagT', bound=_EnumFlag)


if TYPE_CHECKING:
    _ComparatorBase = TypeEngine.Comparator['TSVector']

    class _TypeDecorator(TypeDecorator[_T]):
        ...

else:
    _ComparatorBase = TSVECTOR.Comparator

    class _TypeDecorator(TypeDecorator, Generic[_T]):
        ...


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
        if value is None:
            return None

        return value.value

    def process_result_value(self, value: int | None, dialect: object) -> _FlagT | None:
        if value is None:
            return None

        return self._flag_cls(value)


class DateTime(_TypeDecorator[pendulum.DateTime]):
    impl = TIMESTAMP
    cache_ok = True

    def __init__(self, timezone: bool = False, precision: int | None = None) -> None:
        super().__init__(timezone=timezone, precision=precision)

    def process_bind_param(
        self, value: pendulum.DateTime | None, dialect: object
    ) -> datetime | None:
        if value is None:
            return None

        if not self.impl.timezone:
            value = value.naive()

        return value

    def process_result_value(
        self, value: datetime | None, dialect: object
    ) -> pendulum.DateTime | None:
        if value is None:
            return None

        if self.impl.timezone:
            # `asyncpg` always returns `datetime` in UTC for `timestamp with time zone`
            # columns. However `pendulum` doesn't convert the native UTC constant
            # to `pendulum.UTC`.
            tzinfo = pendulum.UTC
        else:
            tzinfo = None

        return pendulum.instance(value).replace(tzinfo=tzinfo)


class Time(_TypeDecorator[pendulum.Time]):
    impl = TIME
    cache_ok = True

    def __init__(self, precision: int | None = None) -> None:
        super().__init__(timezone=False, precision=precision)

    def process_bind_param(
        self, value: pendulum.Time | None, dialect: object
    ) -> time | None:
        if value is None:
            return None

        return value.replace(tzinfo=None)

    def process_result_value(
        self, value: time | None, dialect: object
    ) -> pendulum.Time | None:
        if value is None:
            return None

        return pendulum.Time(
            value.hour, value.minute, value.second, value.microsecond, tzinfo=None
        )


class Timezone(_TypeDecorator[_Timezone]):
    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: _Timezone | None, dialect: object
    ) -> str | None:
        if value is None:
            return None

        return value.name

    def process_result_value(
        self, value: str | None, dialect: object
    ) -> _Timezone | None:
        if value is None:
            return None

        return pendulum.timezone(value)

    def copy(self, /, **kwargs: object) -> Timezone:
        return Timezone(self.impl.length)
