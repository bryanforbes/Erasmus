from __future__ import annotations

import datetime
import logging
from itertools import chain
from typing import TYPE_CHECKING, Final, cast

import async_timeout
import discord
import pendulum
from attrs import define, field
from botus_receptus import re, utils
from bs4 import BeautifulSoup, SoupStrainer
from discord import app_commands
from discord.ext import tasks
from sqlalchemy import select

from ...data import Passage, VerseRange
from ...db import Session, VerseOfTheDay
from ...db.bible import BibleVersion
from ...exceptions import (
    DoNotUnderstandError,
    ErasmusError,
    InvalidTimeError,
    InvalidTimeZoneError,
)
from ...utils import send_passage

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing_extensions import Self, Unpack

    from botus_receptus.types import Coroutine

    from ...erasmus import Erasmus
    from ...l10n import FormatKwargs, Localizer, MessageLocalizer
    from ...service_manager import ServiceManager
    from ...types import Bible as _BibleType
    from .cog import Bible

_log = logging.getLogger(__name__)

_invite_re = re.compile('\\(\u2068(https://[^\u2069]+?)\u2069\\)')


def _format_with_invite(
    localizer: MessageLocalizer, attribute_id: str, /, **kwargs: Unpack[FormatKwargs]
) -> str:
    return _invite_re.sub(r'(\1)', localizer.format(attribute_id, **kwargs))


_TASK_INTERVAL: Final = 15
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


class _TimeTransformer(app_commands.Transformer):
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

        if (remainder := minutes % _TASK_INTERVAL) > 0:
            minutes += _TASK_INTERVAL - remainder

        if match['ampm']:
            meridian = match['ampm'].lower()

            if meridian == 'am' and hours == 12:
                hours = 0
            if meridian == 'pm' and hours < 12:
                hours += 12

        if minutes > 59:
            if hours >= 23:
                hours = 0
            else:
                hours += 1

            minutes = 0

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


class _TimeZoneTransformer(app_commands.Transformer):
    timezones: list[_TimeZoneItem] = [
        _TimeZoneItem.create(zone) for zone in pendulum.tz.timezones
    ]
    valid_tz_input: set[str] = set(
        chain.from_iterable(
            [
                [zone.replace('_', ' ').lower(), zone.lower()]
                for zone in pendulum.tz.timezones
            ]
        )
    )

    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        if value.lower() not in self.valid_tz_input:
            raise InvalidTimeZoneError(value)

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


_shared_cooldown = app_commands.checks.cooldown(
    rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


@define(frozen=True)
class VerseOfTheDayFetcher:
    verse_range: VerseRange
    service_manager: ServiceManager
    passage_map: dict[int, Passage] = field(init=False, factory=dict)

    async def __call__(self, bible: _BibleType, /) -> Passage:
        if bible.id in self.passage_map:
            return self.passage_map[bible.id]

        passage = await self.service_manager.get_passage(bible, self.verse_range)
        self.passage_map[bible.id] = passage

        return passage


class VerseOfTheDayGroup(
    app_commands.Group, name='verse-of-the-day', description='Verse of the day'
):
    bot: Erasmus
    service_manager: ServiceManager
    localizer: Localizer

    __fetcher: VerseOfTheDayFetcher | None

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.bot = cog.bot
        self.service_manager = cog.service_manager
        self.localizer = cog.localizer

        self.__fetcher = None

    def __get_webhook(self, votd: VerseOfTheDay, /) -> discord.Webhook:
        return discord.Webhook.from_url(
            f'https://discord.com/api/webhooks/{votd.url}', session=self.bot.session
        )

    async def __remove_webhooks(
        self,
        itx: discord.Interaction,
        guild: discord.Guild,
        /,
    ) -> None:
        me = guild.me

        for webhook in await guild.webhooks():
            if webhook.user == me:
                await webhook.delete(
                    reason=f'{itx.user} ({itx.user.id}) updated the verse of the '
                    'day settings for Erasmus'
                )

    async def __get_votd(self) -> VerseRange:
        async with async_timeout.timeout(10), self.bot.session.get(
            'https://www.biblegateway.com/reading-plans/verse-of-the-day'
            '/next?interface=print'
        ) as response:
            text = await response.text(errors='replace')
            strainer = SoupStrainer(
                class_=re.compile(
                    re.WORD_BOUNDARY,
                    'rp-passage-display',
                    re.WORD_BOUNDARY,
                )
            )
            soup = BeautifulSoup(text, 'html.parser', parse_only=strainer)
            passage_node = soup.select_one('.rp-passage-display')

            if passage_node is None:
                raise DoNotUnderstandError

            return VerseRange.from_string(passage_node.get_text(''))

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        channel='The channel to post the verse of the day to',
        time='The time to post at',
        timezone='The time zone for the time to post',
    )
    async def set(
        self,
        itx: discord.Interaction,
        /,
        channel: discord.TextChannel | discord.Thread,
        time: app_commands.Transform[tuple[int, int], _TimeTransformer],
        timezone: app_commands.Transform[str, _TimeZoneTransformer],
    ) -> None:
        assert itx.guild is not None

        if isinstance(channel, discord.Thread):
            thread_id = channel.id
            actual_channel = cast(
                'discord.TextChannel | discord.ForumChannel',
                await itx.guild.fetch_channel(channel.parent_id),
            )
        else:
            thread_id = None
            actual_channel = channel

        localizer = self.localizer.for_message(
            'serverprefs__verse-of-the-day__set', locale=itx.locale
        )

        if not itx.guild.me.guild_permissions & discord.Permissions(
            manage_webhooks=True
        ):
            await utils.send_embed_error(
                itx,
                description=_format_with_invite(
                    localizer,
                    'need-guild-webhooks-permission',
                    data={'invite_url': self.bot.invite_url},
                ),
            )
            return

        if not actual_channel.permissions_for(itx.guild.me) & discord.Permissions(
            manage_webhooks=True
        ):
            await utils.send_embed_error(
                itx,
                description=localizer.format(
                    'need-channel-webhooks-permission',
                    data={
                        'channel': channel.mention,
                        'actual_channel': actual_channel.mention,
                    },
                ),
            )
            return

        await self.__remove_webhooks(itx, itx.guild)
        webhook = await actual_channel.create_webhook(name='Erasmus Verse of the Day')

        now = pendulum.now(tz=timezone)
        next_scheduled = now.set(hour=time[0], minute=time[1], second=0, microsecond=0)

        if next_scheduled <= now:
            next_scheduled = next_scheduled.add(hours=24)

        async with Session.begin() as session:
            votd = await session.get(VerseOfTheDay, itx.guild.id)

            if votd is not None:
                updated = True

                votd.channel_id = actual_channel.id
                votd.url = f'{webhook.id}/{webhook.token}'

                if votd.thread_id != thread_id:
                    votd.thread_id = thread_id

                votd.next_scheduled = next_scheduled
            else:
                updated = False
                votd = VerseOfTheDay(
                    guild_id=itx.guild.id,
                    channel_id=actual_channel.id,
                    thread_id=thread_id,
                    url=f'{webhook.id}/{webhook.token}',
                    next_scheduled=next_scheduled,
                )
                session.add(votd)

            await session.commit()

        await utils.send_embed(
            itx,
            description=(
                localizer.format(
                    'updated' if updated else 'started',
                    data={
                        'channel': channel.mention,
                        'next_scheduled': discord.utils.format_dt(votd.next_scheduled),
                    },
                )
            ),
        )

    @app_commands.command()
    @_shared_cooldown
    async def info(self, itx: discord.Interaction, /) -> None:
        assert itx.guild is not None

        localizer = self.localizer.for_message(
            'serverprefs__verse-of-the-day__info', locale=itx.locale
        )

        async with Session.begin() as session:
            votd = await VerseOfTheDay.for_guild(session, itx.guild)

            if votd:
                channel = await itx.guild.fetch_channel(
                    votd.thread_id or votd.channel_id
                )
                await utils.send_embed(
                    itx,
                    title=localizer.format('title'),
                    fields=[
                        {
                            'name': localizer.format('channel'),
                            'value': channel.mention,
                            'inline': False,
                        },
                        {
                            'name': localizer.format('next_scheduled'),
                            'value': discord.utils.format_dt(votd.next_scheduled),
                            'inline': False,
                        },
                    ],
                )
            else:
                await utils.send_embed(itx, description=localizer.format('not_set'))

    @app_commands.command()
    @_shared_cooldown
    async def stop(self, itx: discord.Interaction, /) -> None:
        assert itx.guild is not None

        localizer = self.localizer.for_message(
            'serverprefs__verse-of-the-day__stop', locale=itx.locale
        )

        async with Session.begin() as session:
            votd = await VerseOfTheDay.for_guild(session, itx.guild)

            if votd is not None:
                if not itx.guild.me.guild_permissions & discord.Permissions(
                    manage_webhooks=True
                ):
                    await utils.send_embed_error(
                        itx,
                        description=localizer.format('unable-to-remove-existing'),
                    )
                else:
                    await self.__remove_webhooks(itx, itx.guild)

                await session.delete(votd)

                await utils.send_embed(itx, description=localizer.format('stopped'))
            else:
                await utils.send_embed(itx, description=localizer.format('not_set'))

            await session.commit()

    async def __check_and_post(self) -> None:
        now = pendulum.now().set(second=0, microsecond=0)
        next_scheduled = now.add(hours=24)

        async with Session.begin() as session:
            result = cast(
                'list[VerseOfTheDay]',
                (
                    await session.scalars(
                        select(VerseOfTheDay).filter(
                            VerseOfTheDay.next_scheduled <= now
                        )
                    )
                ).fetchall(),
            )

            if not result:
                return

            verse_range = await self.__get_votd()

            if self.__fetcher is None or self.__fetcher.verse_range != verse_range:
                self.__fetcher = VerseOfTheDayFetcher(verse_range, self.service_manager)

            localizer = self.localizer.for_message('serverprefs__verse-of-the-day')
            title = localizer.format('title')
            fallback = await BibleVersion.get_by_command(session, 'esv')

            for votd in result:
                webhook = self.__get_webhook(votd)

                if votd.prefs is not None and votd.prefs.bible_version is not None:
                    bible = votd.prefs.bible_version
                else:
                    bible = fallback

                passage = await self.__fetcher(bible)

                try:
                    await send_passage(
                        webhook,
                        passage,
                        title=title,
                        thread=discord.Object(votd.thread_id)
                        if votd.thread_id is not None
                        else discord.utils.MISSING,
                        avatar_url='https://i.imgur.com/XQ8N2vH.png',
                    )
                    votd.next_scheduled = next_scheduled
                except (discord.DiscordException, ErasmusError) as error:
                    _log.exception(
                        'An error occurred while posting the verse of the day to guild '
                        'ID %s',
                        votd.guild_id,
                        exc_info=error,
                        stack_info=True,
                    )

            await session.commit()

    def get_task(self) -> tasks.Loop[Callable[[], Coroutine[None]]]:
        return tasks.loop(
            time=[
                datetime.time(*args)
                for args in chain.from_iterable(
                    [(hour, minute) for minute in range(0, 60, _TASK_INTERVAL)]
                    for hour in range(24)
                )
            ],
        )(self.__check_and_post)
