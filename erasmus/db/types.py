from __future__ import annotations

from typing import TYPE_CHECKING

import pendulum
from botus_receptus.sqlalchemy import TypeDecorator
from pendulum.tz.timezone import Timezone as _Timezone
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import TIME, TIMESTAMP

if TYPE_CHECKING:
    from datetime import datetime, time


class DateTime(TypeDecorator[pendulum.DateTime]):
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


class Time(TypeDecorator[pendulum.Time]):
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


class Timezone(TypeDecorator[_Timezone]):
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