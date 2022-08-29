from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING

import discord
from botus_receptus import Cog, Embed, utils
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer


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
                label=localizer.format('invite'),
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
                label=localizer.format('support-server'),
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
        title=localizer.format('title'),
        fields=[
            {'name': localizer.format('guilds'), 'value': str(guild_count)},
            {
                'name': localizer.format('channels'),
                'value': str(channel_count),
            },
        ],
        footer={
            'text': localizer.format('footer', data={'version': dpy_version}),
            'icon_url': 'http://i.imgur.com/5BFecvA.png',
        },
        timestamp=discord.utils.utcnow(),
    )


class Misc(Cog['Erasmus']):
    localizer: Localizer

    def __init__(self, bot: Erasmus, /) -> None:
        super().__init__(bot)

        self.localizer = bot.localizer

    @commands.hybrid_command()
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: commands.Context[Erasmus], /) -> None:
        '''Get a link to invite Erasmus to your server'''

        localizer = self.localizer.for_message(
            'about',
            locale=ctx.interaction.locale if ctx.interaction is not None else None,
        )

        await utils.send(ctx, view=InviteView(self.bot.application_id, localizer))

    @commands.hybrid_command()
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

    @app_commands.command()
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def notice(self, itx: discord.Interaction, /) -> None:
        '''Display text-command deprecation notice'''

        await self.bot._send_application_command_notice(itx)


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))
