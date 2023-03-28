from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Final, cast
from typing_extensions import Self, Unpack, override

import discord
import pendulum
from botus_receptus import re, utils
from discord import app_commands
from pendulum.tz.timezone import Timezone  # noqa: TC002

from ....data import SectionFlag
from ....db import BibleVersion, DailyBread, Session
from ....exceptions import InvalidTimeError, InvalidTimeZoneError
from ....utils import frozen
from .common import TASK_INTERVAL, get_first_scheduled_time

if TYPE_CHECKING:
    from ....erasmus import Erasmus
    from ....l10n import FormatKwargs, GroupLocalizer, MessageLocalizer
    from ..types import ParentGroup

_shared_cooldown: Final = app_commands.checks.cooldown(
    rate=2, per=30.0, key=lambda i: (i.guild_id, i.user.id)
)
_time_re: Final = re.compile(
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
_invite_re: Final = re.compile('\\(\u2068(https://[^\u2069]+?)\u2069\\)')


def _format_with_invite(
    localizer: MessageLocalizer, attribute_id: str, /, **kwargs: Unpack[FormatKwargs]
) -> str:
    return _invite_re.sub(r'(\1)', localizer.format(attribute_id, **kwargs))


def _can_manage_guild_webhooks(guild: discord.Guild, /) -> bool:
    me = guild.me

    if guild.owner_id == me.id:
        return True

    base = discord.Permissions.none()
    for role in me.roles:
        base.value |= role.permissions.value

    if base.administrator:
        return True

    return base.manage_webhooks


def _can_manage_channel_webhooks(
    channel: discord.TextChannel | discord.ForumChannel, /
) -> bool:
    guild = channel.guild
    me = guild.me

    if guild.owner_id == me.id:
        return True

    default = guild.default_role
    base = discord.Permissions(default.permissions.value)

    roles = me._roles
    get_role = guild.get_role

    # Apply guild roles that the member has.
    for role_id in roles:
        role = get_role(role_id)
        if role is not None:
            base.value |= role._permissions

    # Guild-wide Administrator -> True for everything
    # Bypass all channel-specific overrides
    if base.administrator:
        return True

    # Apply @everyone allow/deny first since it's special
    try:
        maybe_everyone = channel._overwrites[0]
        if maybe_everyone.id == guild.id:
            base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            remaining_overwrites = channel._overwrites[1:]
        else:
            remaining_overwrites = channel._overwrites
    except IndexError:
        remaining_overwrites = channel._overwrites

    denies = 0
    allows = 0

    # Apply channel specific role permission overwrites
    for overwrite in remaining_overwrites:
        if overwrite.is_role() and roles.has(overwrite.id):
            denies |= overwrite.deny
            allows |= overwrite.allow

    base.handle_overwrite(allow=allows, deny=denies)

    # Apply member specific permission overwrites
    for overwrite in remaining_overwrites:
        if overwrite.is_member() and overwrite.id == me.id:
            base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
            break

    return base.manage_webhooks


class _TimeTransformer(app_commands.Transformer):
    times = [
        f'{str(12 if hour == 0 else hour)}:{str(minute):0>2} {meridian}'
        for hour, minute, meridian in chain.from_iterable(
            chain.from_iterable(
                [(hour, minute, meridian) for minute in range(0, 60, 15)]
                for hour in range(12)
            )
            for meridian in ('am', 'pm')
        )
    ]

    @override
    async def transform(self, itx: discord.Interaction, value: str, /) -> pendulum.Time:
        value = value.strip()

        if (match := _time_re.match(value)) is None:
            raise InvalidTimeError(value)

        hours = int(match['hours'])
        minutes = int(match['minutes'])

        if (remainder := minutes % TASK_INTERVAL) > 0:
            minutes += TASK_INTERVAL - remainder

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

        return pendulum.Time(hours, minutes)

    @override
    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        current = current.strip().lower()
        return [
            app_commands.Choice(name=time.upper(), value=time)
            for time in self.times
            if not current or current in time
        ][:25]


@frozen
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
        _TimeZoneItem.create(zone) for zone in pendulum.timezones
    ]
    tz_map: dict[str, str] = dict(
        chain.from_iterable(
            [
                [(zone.replace('_', ' ').lower(), zone), (zone.lower(), zone)]
                for zone in pendulum.timezones
            ]
        )
    )

    @override
    async def transform(self, itx: discord.Interaction, value: str, /) -> Timezone:
        value_lower = value.lower()

        if value_lower not in self.tz_map:
            raise InvalidTimeZoneError(value)

        return pendulum.timezone(self.tz_map[value_lower])

    @override
    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        current = current.strip().lower()
        return [
            app_commands.Choice(name=zone.name, value=zone.value)
            for zone in self.timezones
            if not current or current in zone.name_lower
        ][:25]


class DailyBreadPreferencesGroup(
    app_commands.Group, name='daily-bread', description='Daily bread settings'
):
    bot: Erasmus
    localizer: GroupLocalizer

    def initialize_from_parent(self, parent: ParentGroup, /) -> None:
        self.bot = parent.bot
        self.localizer = parent.localizer.for_group(self)

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
                    reason=f'{itx.user} ({itx.user.id}) updated the daily bread '
                    'settings for Erasmus'
                )

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        channel='The channel to post the daily bread to',
        time='The time to post at',
        timezone='The time zone for the time to post',
    )
    async def set(
        self,
        itx: discord.Interaction,
        /,
        channel: discord.TextChannel | discord.Thread,
        time: app_commands.Transform[pendulum.Time, _TimeTransformer],
        timezone: app_commands.Transform[Timezone, _TimeZoneTransformer],
    ) -> None:
        '''Set or update the automated daily bread post settings for this server'''

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

        localizer = self.localizer.for_message('set', locale=itx.locale)

        if not _can_manage_guild_webhooks(itx.guild):
            await utils.send_embed_error(
                itx,
                description=_format_with_invite(
                    localizer,
                    'need-guild-webhooks-permission',
                    data={'invite_url': self.bot.invite_url},
                ),
            )
            return

        if not _can_manage_channel_webhooks(actual_channel):
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
        webhook = await actual_channel.create_webhook(name='Daily Bread from Erasmus')

        next_scheduled = get_first_scheduled_time(time, timezone)

        async with Session.begin() as session:
            daily_bread = await DailyBread.for_guild(session, itx.guild)

            if daily_bread is not None:
                updated = True

                daily_bread.channel_id = actual_channel.id
                daily_bread.url = f'{webhook.id}/{webhook.token}'

                if daily_bread.thread_id != thread_id:
                    daily_bread.thread_id = thread_id

                daily_bread.time = time
                daily_bread.timezone = timezone
                daily_bread.next_scheduled = next_scheduled
            else:
                updated = False
                daily_bread = DailyBread(
                    guild_id=itx.guild.id,
                    channel_id=actual_channel.id,
                    thread_id=thread_id,
                    url=f'{webhook.id}/{webhook.token}',
                    next_scheduled=next_scheduled,
                    time=time,
                    timezone=timezone,
                )
                session.add(daily_bread)

            version = await BibleVersion.get_for(session, guild=itx.guild)

            await session.commit()

        if (SectionFlag.OT | SectionFlag.NT) not in version.books:
            await utils.send_embed(
                itx,
                description=(
                    localizer.format('version-warning', data={'version': version.name})
                ),
                color=discord.Color.yellow(),
            )

        await utils.send_embed(
            itx,
            description=(
                localizer.format(
                    'updated' if updated else 'started',
                    data={
                        'channel': channel.mention,
                        'next_scheduled': discord.utils.format_dt(
                            daily_bread.next_scheduled
                        ),
                        'version': version.name,
                    },
                )
            ),
        )

    @app_commands.command()
    @_shared_cooldown
    async def stop(self, itx: discord.Interaction, /) -> None:
        '''Stop the automated daily bread posts for this server'''

        assert itx.guild is not None

        localizer = self.localizer.for_message('stop', locale=itx.locale)

        async with Session.begin() as session:
            daily_bread = await DailyBread.for_guild(session, itx.guild)

            if daily_bread is not None:
                if not _can_manage_guild_webhooks(itx.guild):
                    await utils.send_embed_error(
                        itx,
                        description=localizer.format('unable-to-remove-existing'),
                        color=discord.Color.yellow(),
                    )
                else:
                    await self.__remove_webhooks(itx, itx.guild)

                await session.delete(daily_bread)

                await utils.send_embed(itx, description=localizer.format('stopped'))
            else:
                await utils.send_embed(itx, description=localizer.format('not_set'))

            await session.commit()
