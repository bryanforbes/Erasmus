from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pendulum

if TYPE_CHECKING:
    from pendulum.tz.timezone import Timezone

TASK_INTERVAL: Final = 15


def get_next_scheduled_time(
    previous_date_utc: pendulum.DateTime,
    time: pendulum.Time,
    timezone: Timezone,
    /,
) -> pendulum.DateTime:
    now = pendulum.now(pendulum.UTC)

    next_date_utc = previous_date_utc.replace(
        year=now.year, month=now.month, day=now.day
    ).add(hours=24)

    previous_dst_offset = timezone.dst(previous_date_utc)
    next_dst_offset = timezone.dst(next_date_utc)

    if previous_dst_offset and not next_dst_offset:
        # Standard -> DST
        next_date_utc = next_date_utc - previous_dst_offset
    elif not previous_dst_offset and next_dst_offset:
        # DST -> Standard
        next_date_utc = next_date_utc + next_dst_offset

    next_date = next_date_utc.astimezone(timezone)

    return next_date.set(hour=time.hour, minute=time.minute, second=0).astimezone(
        pendulum.UTC
    )


def get_first_scheduled_time(
    time: pendulum.Time, timezone: Timezone, /
) -> pendulum.DateTime:
    now = pendulum.now(pendulum.UTC)

    first_time = (
        now.astimezone(timezone)
        .set(hour=time.hour, minute=time.minute, second=0, microsecond=0)
        .astimezone(pendulum.UTC)
    )

    if first_time > now:
        return first_time

    return get_next_scheduled_time(first_time, time, timezone)
