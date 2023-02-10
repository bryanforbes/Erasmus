from __future__ import annotations

from typing import TYPE_CHECKING

import pendulum
import pytest

from erasmus.cogs.bible.daily_bread.common import (
    get_first_scheduled_time,
    get_next_scheduled_time,
)

if TYPE_CHECKING:
    from ....types import MockerFixture


@pytest.mark.parametrize(
    'now_time,start_time,time_args,tz,expected_time',
    [
        (
            '2022-06-25T11:00:00',  # now
            '2022-06-25T11:00:00',  # previous date
            (6, 0),
            'US/Central',
            '2022-06-26T11:00:00',  # expected
        ),
        (
            '2022-06-25T13:01:01',  # now
            '2022-06-25T08:01:01',  # previous date
            (6, 0),
            'US/Central',
            '2022-06-26T11:00:00',  # expected
        ),
        # Standard 2AM -> DST 3AM
        (
            '2022-03-12T07:00:00',  # now
            '2022-03-12T07:00:00',  # previous date
            (2, 0),
            'US/Eastern',
            '2022-03-13T07:00:00',  # expected
        ),
        # DST 3AM -> DST 2AM
        (
            '2022-03-13T07:00:00',  # now
            '2022-03-13T07:00:00',  # previous date
            (2, 0),
            'US/Eastern',
            '2022-03-14T06:00:00',  # expected
        ),
        # Standard 2AM -> DST 3AM
        (
            '2022-03-12T07:00:00',  # now
            '2022-03-10T07:00:00',  # previous date (2 days prior)
            (2, 0),
            'US/Eastern',
            '2022-03-13T07:00:00',  # expected
        ),
        # DST 2AM -> Standard 2AM
        (
            '2022-11-05T06:00:00',  # now
            '2022-11-05T06:00:00',  # previous date
            (2, 0),
            'US/Eastern',
            '2022-11-06T07:00:00',  # expected
        ),
    ],
)
def test_get_next_scheduled_time(
    mocker: MockerFixture,
    tz: str,
    now_time: str,
    start_time: str,
    time_args: tuple[int, int],
    expected_time: str,
) -> None:
    tzinfo = pendulum.timezone(tz)

    now = mocker.patch('pendulum.now')
    now.return_value = pendulum.DateTime.strptime(now_time, '%Y-%m-%dT%H:%M:%S')

    assert get_next_scheduled_time(
        pendulum.DateTime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'),
        pendulum.Time(time_args[0], time_args[1]),
        tzinfo,
    ) == pendulum.DateTime.strptime(expected_time, '%Y-%m-%dT%H:%M:%S')


@pytest.mark.parametrize(
    'start_time,time_args,tz_name,expected_time',
    [
        ('2022-03-01T10:00:00', (5, 0), 'US/Eastern', '2022-03-28T09:00:00'),
        ('2022-11-01T10:00:00', (6, 0), 'US/Eastern', '2022-11-28T11:00:00'),
        ('2022-03-02T05:15:00', (23, 15), 'US/Central', '2022-03-29T04:15:00'),
        ('2022-11-02T04:15:00', (23, 15), 'US/Central', '2022-11-29T05:15:00'),
        ('2022-03-01T05:00:00', (5, 0), 'UTC', '2022-03-28T05:00:00'),
        ('2022-11-01T06:00:00', (6, 0), 'UTC', '2022-11-28T06:00:00'),
        ('2022-03-01T20:15:00', (23, 45), 'Iran', '2022-03-28T19:15:00'),
        ('2022-09-01T19:15:00', (23, 45), 'Iran', '2022-09-28T20:15:00'),
    ],
)
def test_get_next_scheduled_time_month(
    mocker: MockerFixture,
    start_time: str,
    time_args: tuple[int, int],
    tz_name: str,
    expected_time: str,
) -> None:
    now = mocker.patch('pendulum.now')
    actual = pendulum.DateTime.strptime(start_time, '%Y-%m-%dT%H:%M:%S').astimezone(
        pendulum.UTC
    )
    tz = pendulum.timezone(tz_name)

    for _ in range(1, 28):
        now.return_value = actual
        actual = get_next_scheduled_time(actual, pendulum.Time(*time_args), tz)

    assert actual == pendulum.DateTime.strptime(expected_time, '%Y-%m-%dT%H:%M:%S')


@pytest.mark.parametrize(
    'now_time,time_args,tz,expected_time',
    [
        (
            '2022-06-25T11:00:00',  # now (6am CDT)
            (5, 0),
            'US/Central',
            '2022-06-26T10:00:00',  # expected (5am CDT next day)
        ),
        (
            '2022-06-25T11:00:00',  # now (6am CDT)
            (6, 0),
            'US/Central',
            '2022-06-26T11:00:00',  # expected (6am CDT next day)
        ),
        (
            '2022-06-25T11:00:00',  # now (6am CDT)
            (7, 0),
            'US/Central',
            '2022-06-25T12:00:00',  # expected (7am CDT)
        ),
        (
            '2022-11-05T11:00:00',  # now (6am CDT)
            (5, 0),
            'US/Central',
            '2022-11-06T11:00:00',  # expected (5am CST next day)
        ),
        (
            '2022-11-05T11:00:00',  # now (6am CDT)
            (6, 0),
            'US/Central',
            '2022-11-06T12:00:00',  # expected (6am CST next day)
        ),
        (
            '2022-11-05T11:00:00',  # now (6am CDT)
            (7, 0),
            'US/Central',
            '2022-11-05T12:00:00',  # expected (7am CDT)
        ),
        (
            '2022-03-12T12:00:00',  # now (6am CST)
            (5, 0),
            'US/Central',
            '2022-03-13T10:00:00',  # expected (5am CDT next day)
        ),
        (
            '2022-03-12T12:00:00',  # now (6am CST)
            (6, 0),
            'US/Central',
            '2022-03-13T11:00:00',  # expected (6am CDT next day)
        ),
        (
            '2022-03-12T12:00:00',  # now (6am CST)
            (7, 0),
            'US/Central',
            '2022-03-12T13:00:00',  # expected (7am CST)
        ),
    ],
)
def test_get_first_scheduled_time(
    mocker: MockerFixture,
    tz: str,
    now_time: str,
    time_args: tuple[int, int],
    expected_time: str,
) -> None:
    tzinfo = pendulum.timezone(tz)

    now = mocker.patch('pendulum.now')
    now.return_value = pendulum.DateTime.strptime(now_time, '%Y-%m-%dT%H:%M:%S')

    assert get_first_scheduled_time(
        pendulum.Time(time_args[0], time_args[1]),
        tzinfo,
    ) == pendulum.DateTime.strptime(expected_time, '%Y-%m-%dT%H:%M:%S')
