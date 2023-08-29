from __future__ import annotations

from datetime import UTC, datetime, time

import pendulum
import pytest
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import TIME, TIMESTAMP

from erasmus.db.types import DateTime, Time, Timezone


class TestDateTime:
    def test_init(self) -> None:
        dt = DateTime()
        dt_tz = DateTime(timezone=True, precision=4)

        assert isinstance(dt.impl, TIMESTAMP)
        assert isinstance(dt_tz.impl, TIMESTAMP)

        assert not dt.impl.timezone
        assert dt.impl.precision is None

        assert dt_tz.impl.timezone
        assert dt_tz.impl.precision == 4

    @pytest.mark.parametrize(
        'timezone,bind_param,expected',
        [
            (
                True,
                pendulum.datetime(2020, 6, 26, 5, tz='US/Central'),
                pendulum.datetime(2020, 6, 26, 5, tz='US/Central'),
            ),
            (True, None, None),
            (
                False,
                pendulum.datetime(2020, 6, 26, 5, tz='US/Central'),
                pendulum.datetime(2020, 6, 26, 5, tz=None),
            ),
            (False, None, None),
        ],
    )
    def test_process_bind_param(
        self,
        timezone: bool,
        bind_param: pendulum.DateTime | None,
        expected: datetime | None,
    ) -> None:
        dt = DateTime(timezone=timezone)

        actual = dt.process_bind_param(bind_param, object())

        if expected is None:
            assert actual is None
        else:
            assert isinstance(actual, datetime)
            assert actual == expected

            if timezone:
                assert actual.tzinfo is not None
            else:
                assert actual.tzinfo is None

    @pytest.mark.parametrize(
        'timezone,result_value,expected',
        [
            (
                True,
                datetime(2020, 6, 26, 5, tzinfo=UTC),
                pendulum.datetime(2020, 6, 26, 5, tz=pendulum.UTC),
            ),
            (
                False,
                datetime(2020, 6, 26, 5),
                pendulum.datetime(2020, 6, 26, 5, tz=None),
            ),
            (True, None, None),
        ],
    )
    def test_process_result_value(
        self,
        timezone: bool,
        result_value: datetime | None,
        expected: pendulum.DateTime | None,
    ) -> None:
        dt = DateTime(timezone=timezone)

        actual = dt.process_result_value(result_value, object())

        if expected is None:
            assert actual is None
        else:
            assert isinstance(actual, pendulum.DateTime)
            assert actual == expected

            if timezone:
                assert actual.timezone is pendulum.UTC
            else:
                assert actual.timezone is None


class TestTime:
    def test_init(self) -> None:
        tm = Time()
        tm_precision = Time(precision=4)

        assert isinstance(tm.impl, TIME)
        assert isinstance(tm_precision.impl, TIME)

        assert not tm.impl.timezone
        assert not tm_precision.impl.timezone

        assert tm.impl.precision is None
        assert tm_precision.impl.precision == 4

    @pytest.mark.parametrize(
        'bind_param,expected',
        [
            (
                pendulum.Time(5, 15, tzinfo=pendulum.timezone('US/Central')),
                pendulum.Time(5, 15, tzinfo=None),
            ),
            (None, None),
        ],
    )
    def test_process_bind_param(
        self,
        bind_param: pendulum.Time | None,
        expected: time | None,
    ) -> None:
        tm = Time()

        actual = tm.process_bind_param(bind_param, object())

        if expected is None:
            assert actual is None
        else:
            assert isinstance(actual, time)
            assert actual == expected
            assert actual.tzinfo is None

    @pytest.mark.parametrize(
        'result_value,expected',
        [
            (
                time(5, 30, 1, 2, tzinfo=UTC),
                pendulum.Time(5, 30, 1, 2, tzinfo=None),
            ),
            (None, None),
        ],
    )
    def test_process_result_value(
        self,
        result_value: time | None,
        expected: pendulum.Time | None,
    ) -> None:
        tm = Time()

        actual = tm.process_result_value(result_value, object())

        if expected is None:
            assert actual is None
        else:
            assert isinstance(actual, pendulum.Time)
            assert actual == expected
            assert actual.tzinfo is None


class TestTimezone:
    def test_init(self) -> None:
        tz = Timezone()

        assert isinstance(tz.impl, String)

    @pytest.mark.parametrize('tz_name', ['US/Central', 'UTC', 'America/New_York', None])
    def test_process_bind_param(self, tz_name: str | None) -> None:
        tz = Timezone()

        assert (
            tz.process_bind_param(
                tz_name if tz_name is None else pendulum.timezone(tz_name), object()
            )
            == tz_name
        )

    @pytest.mark.parametrize('tz_name', ['US/Central', 'UTC', 'America/New_York', None])
    def test_process_result_value(self, tz_name: str | None) -> None:
        tz = Timezone()

        assert tz.process_result_value(tz_name, object()) == (
            tz_name if tz_name is None else pendulum.timezone(tz_name)
        )
