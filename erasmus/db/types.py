from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import Self, override

import pendulum
from pendulum.tz.timezone import Timezone as _Timezone
from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.postgresql import TIME, TIMESTAMP

if TYPE_CHECKING:
    from datetime import datetime, time


class DateTime(TypeDecorator[pendulum.DateTime]):
    impl: TIMESTAMP = TIMESTAMP  # pyright: ignore[reportGeneralTypeIssues]
    cache_ok = True

    def __init__(
        self,
        timezone: bool = False,  # noqa: FBT001, FBT002
        precision: int | None = None,
    ) -> None:
        super().__init__(timezone=timezone, precision=precision)

    @override
    def process_bind_param(
        self, value: pendulum.DateTime | None, dialect: object
    ) -> datetime | None:
        if value is None:
            return None

        if not self.impl.timezone:
            return value.naive()

        return value

    @override
    def process_result_value(
        self, value: datetime | None, dialect: object
    ) -> pendulum.DateTime | None:
        if value is None:
            return None

        if self.impl.timezone:  # noqa: SIM108
            # `asyncpg` always returns `datetime` in UTC for `timestamp with time zone`
            # columns. However `pendulum` doesn't convert the native UTC constant
            # to `pendulum.UTC`.
            tzinfo = pendulum.UTC
        else:
            tzinfo = None

        return pendulum.instance(value).replace(tzinfo=tzinfo)


class Time(TypeDecorator[pendulum.Time]):
    impl: TIME = TIME  # pyright: ignore[reportGeneralTypeIssues]
    cache_ok = True

    def __init__(self, precision: int | None = None) -> None:
        super().__init__(timezone=False, precision=precision)

    @override
    def process_bind_param(
        self, value: pendulum.Time | None, dialect: object
    ) -> time | None:
        if value is None:
            return None

        return value.replace(tzinfo=None)

    @override
    def process_result_value(
        self, value: time | None, dialect: object
    ) -> pendulum.Time | None:
        if value is None:
            return None

        return pendulum.Time(
            value.hour, value.minute, value.second, value.microsecond, tzinfo=None
        )


class Timezone(TypeDecorator[_Timezone]):
    impl: String = String  # pyright: ignore[reportGeneralTypeIssues]
    cache_ok = True

    @override
    def process_bind_param(
        self, value: _Timezone | None, dialect: object
    ) -> str | None:
        if value is None:
            return None

        return value.name

    @override
    def process_result_value(
        self, value: str | None, dialect: object
    ) -> _Timezone | None:
        if value is None:
            return None

        return pendulum.timezone(value)

    @override
    def copy(self, /, **kwargs: object) -> Self:
        return Timezone(self.impl.length)
