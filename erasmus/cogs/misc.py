from __future__ import annotations

from importlib import metadata
from typing import Any

import discord
from botus_receptus import Cog, Embed, utils
from discord import app_commands
from discord.ext import commands

from ..erasmus import Erasmus
from ..l10n import Localizer, MessageLocalizer, attribute_str, message_str


def _(message_id: str, /, **kwargs: Any) -> app_commands.locale_str:
    return message_str(message_id, resource='misc', **kwargs)


def _d(message_id: str, /, **kwargs: Any) -> app_commands.locale_str:
    return attribute_str(message_id, 'description', resource='misc', **kwargs)


class InviteView(discord.ui.View):
    def __init__(
        self,
        application_id: int,
        localizer: MessageLocalizer,
        /,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(timeout=timeout)

        perms = discord.Permissions(
            add_reactions=True,
            embed_links=True,
            manage_messages=True,
            read_message_history=True,
            read_messages=True,
            send_messages=True,
            send_messages_in_threads=True,
        )

        self.add_item(
            discord.ui.Button(
                label=localizer.format_attribute('invite'),
                url=discord.utils.oauth_url(application_id, permissions=perms),
            )
        )


class AboutView(InviteView):
    def __init__(
        self,
        application_id: int,
        localizer: MessageLocalizer,
        /,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(application_id, localizer, timeout=timeout)

        self.add_item(
            discord.ui.Button(
                label=localizer.format_attribute('support-server'),
                url='https://discord.gg/ncZtNu5zgs',
            )
        )

        self.add_item(
            discord.ui.Button(
                label='Github', url='https://github.com/bryanforbes/Erasmus'
            )
        )


def get_about_embed(bot: Erasmus, localizer: MessageLocalizer) -> Embed:
    channel_count = 0
    guild_count = 0

    for guild in bot.guilds:
        guild_count += 1

        if guild.unavailable or guild.member_count is None:
            continue

        channels = filter(lambda c: isinstance(c, discord.TextChannel), guild.channels)
        channel_count += len(list(channels))

    dpy_version = metadata.distribution('discord.py').version

    return Embed(
        title=localizer.format_message(),
        fields=[
            {'name': localizer.format_attribute('guilds'), 'value': str(guild_count)},
            {
                'name': localizer.format_attribute('channels'),
                'value': str(channel_count),
            },
        ],
        footer={
            'text': localizer.format_attribute('footer', {'version': dpy_version}),
            'icon_url': 'http://i.imgur.com/5BFecvA.png',
        },
        timestamp=discord.utils.utcnow(),
    )


class Misc(Cog[Erasmus]):
    localizer: Localizer

    def __init__(self, bot: Erasmus, /) -> None:
        super().__init__(bot)

        self.localizer = bot.app_localizer.for_resource('misc')

    @commands.hybrid_command(name=_('invite'), description=_d('invite'))
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: commands.Context[Erasmus], /) -> None:
        '''Get a link to invite Erasmus to your server'''

        localizer = self.localizer.for_message(
            'about',
            locale=ctx.interaction.locale if ctx.interaction is not None else None,
        )

        await utils.send(ctx, view=InviteView(self.bot.application_id, localizer))

    @commands.hybrid_command(name=_('about'), description=_d('about'))
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    async def about(self, ctx: commands.Context[Erasmus], /) -> None:
        '''Get info about Erasmus'''

        localizer = self.localizer.for_message(
            'about',
            locale=ctx.interaction.locale if ctx.interaction is not None else None,
        )

        await utils.send(
            ctx,
            embeds=[get_about_embed(self.bot, localizer)],
            view=AboutView(self.bot.application_id, localizer),
        )

    @app_commands.command(name=_('notice'), description=_d('notice'))
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def notice(self, interaction: discord.Interaction, /) -> None:
        '''Display text-command deprecation notice'''

        await self.bot._application_command_notice(interaction, skip_check=True)


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))
