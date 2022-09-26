from __future__ import annotations

import datetime
from itertools import chain
from typing import TYPE_CHECKING, cast

import aiohttp
import discord
import pendulum
from attrs import define
from botus_receptus import re, utils
from discord import app_commands
from discord.ext import tasks
from sqlalchemy import select

from ...db import GuildVotd, Session
from ...exceptions import InvalidTimeError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing_extensions import Self

    from . import Bible

_time_re = re.compile(
    re.START,
    re.either(
        re.named_group('hours')(
            re.either(
                re.named_group('meridian_hours')(re.either('0?[1-9]', '1[0-2]')),
                '00',
                '1[3-9]',
                '2[0-3]',
            ),
        )
    ),
    re.any_number_of(re.WHITESPACE),
    ':',
    re.any_number_of(re.WHITESPACE),
    re.named_group('minutes')(r'[0-5][0-9]'),
    re.if_group(
        'meridian_hours',
        re.optional(
            re.any_number_of(re.WHITESPACE),
            re.named_group('ampm')(r'[ap]m'),
        ),
    ),
    re.END,
    flags=re.IGNORECASE,
)


class TimeTransformer(app_commands.Transformer):
    times = [
        f'{str(12 if hour == 0 else hour):0>2}:{str(minute):0>2} {meridian}'
        for hour, minute, meridian in chain.from_iterable(
            chain.from_iterable(
                [(hour, minute, meridian) for minute in range(0, 60, 15)]
                for hour in range(12)
            )
            for meridian in ('am', 'pm')
        )
    ]

    async def transform(
        self, itx: discord.Interaction, value: str, /
    ) -> tuple[int, int]:
        value = value.strip()

        if (match := _time_re.match(value)) is None:
            raise InvalidTimeError(value)

        hours = int(match['hours'])
        minutes = int(match['minutes'])

        if match['ampm']:
            meridian = match['ampm'].lower()

            if meridian == 'am' and hours == 12:
                hours = 0
            if meridian == 'pm' and hours < 12:
                hours += 12

        return hours, minutes

    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        current = current.strip().lower()
        return [
            app_commands.Choice(name=time.upper(), value=time)
            for time in self.times
            if not current or current in time
        ][:25]


@define(frozen=True)
class _TimeZoneItem:
    name: str
    name_lower: str
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        name = value.replace('_', ' ')
        return _TimeZoneItem(name=name, name_lower=name.lower(), value=value)


class TimeZoneTransformer(app_commands.Transformer):
    timezones: list[_TimeZoneItem] = [
        _TimeZoneItem.create(zone) for zone in pendulum.tz.timezones
    ]

    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        return value

    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        current = current.strip().lower()
        return [
            app_commands.Choice(name=zone.name, value=zone.value)
            for zone in self.timezones
            if not current or current in zone.name_lower
        ][:25]


class VerseOfTheDayGroup(
    app_commands.Group, name='verse-of-the-day', description='Verse of the day'
):
    session: aiohttp.ClientSession

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.session = cog.bot.session
        # self.localizer = cog.localizer

    @app_commands.command()
    async def set(
        self,
        itx: discord.Interaction,
        /,
        channel: discord.TextChannel,
        time: app_commands.Transform[tuple[int, int], TimeTransformer],
        timezone: app_commands.Transform[str, TimeZoneTransformer],
    ) -> None:
        assert itx.guild is not None

        now = pendulum.now(tz=timezone)
        next_scheduled = now.set(hour=time[0], minute=time[1], second=0, microsecond=0)

        if next_scheduled <= now:
            next_scheduled = next_scheduled.add(hours=24)

        async with Session.begin() as session:
            votd = await session.get(GuildVotd, itx.guild.id)

            if votd is not None:
                if votd.channel_id != channel.id:
                    webhook = discord.Webhook.from_url(
                        f'https://discord.com/api/webhooks/{votd.webhook}',
                        session=self.session,
                    )
                    await webhook.delete()
                    webhook = await channel.create_webhook(
                        name='Erasmus Verse of the Day'
                    )
                    votd.webhook = f'{webhook.id}/{webhook.token}'

                votd.next_scheduled = next_scheduled
            else:
                webhook = await channel.create_webhook(name='Erasmus Verse of the Day')
                votd = GuildVotd(
                    guild_id=itx.guild.id,
                    channel_id=channel.id,
                    webhook=f'{webhook.id}/{webhook.token}',
                    next_scheduled=next_scheduled,
                )
                session.add(votd)

            await session.commit()

        await utils.send_embed(
            itx, description='Verse of the day started for this server'
        )

    @app_commands.command()
    async def info(self, itx: discord.Interaction, /) -> None:
        assert itx.guild is not None

        async with Session.begin() as session:
            votd = await GuildVotd.for_guild(session, itx.guild)

            if votd:
                channel = await itx.guild.fetch_channel(votd.channel_id)
                await utils.send_embed(
                    itx,
                    title='Verse of the Day Information',
                    fields=[
                        {'name': 'Channel', 'value': channel.mention, 'inline': False},
                        {
                            'name': 'Next Scheduled',
                            'value': discord.utils.format_dt(votd.next_scheduled),
                            'inline': False,
                        },
                    ],
                )
            else:
                await utils.send_embed(itx, description='No verse of the day set')

    @app_commands.command()
    async def stop(self, itx: discord.Interaction, /) -> None:
        assert itx.guild is not None

        async with Session.begin() as session:
            votd = await GuildVotd.for_guild(session, itx.guild)

            if votd is not None:
                webhook = discord.Webhook.from_url(
                    f'https://discord.com/api/webhooks/{votd.webhook}',
                    session=self.session,
                )
                await webhook.delete()
                await session.delete(votd)

                await utils.send_embed(
                    itx, description='Verse of the day stopped for this server'
                )
            else:
                await utils.send_embed(itx, description='No verse of the day set')

    @tasks.loop(
        time=[
            datetime.time(*args)
            for args in chain.from_iterable(
                [(hour, minute) for minute in range(0, 60, 15)] for hour in range(24)
            )
        ]
    )
    async def __task(self) -> None:
        now = pendulum.now().set(second=0, microsecond=0)

        async with Session.begin() as session:
            result = cast(
                'Iterable[GuildVotd]',
                await session.scalars(
                    select(GuildVotd).filter(GuildVotd.next_scheduled <= now)
                ),
            )

            print(list(result))

    async def start_task(self) -> None:
        self.__task.start()

        await self.__task()

    async def stop_task(self) -> None:
        self.__task.cancel()
