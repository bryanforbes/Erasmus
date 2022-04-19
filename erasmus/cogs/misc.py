from __future__ import annotations

from importlib import metadata

import discord
from botus_receptus import Cog, Embed, utils
from discord.ext import commands

from ..erasmus import Erasmus


class InviteView(discord.ui.View):
    def __init__(self, application_id: int, /, *, timeout: float | None = 180) -> None:
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
                label='Invite Erasmus',
                url=discord.utils.oauth_url(application_id, permissions=perms),
            )
        )


class AboutView(InviteView):
    def __init__(self, application_id: int, /, *, timeout: float | None = 180) -> None:
        super().__init__(application_id, timeout=timeout)

        self.add_item(
            discord.ui.Button(
                label='Official Support Server', url='https://discord.gg/ncZtNu5zgs'
            )
        )

        self.add_item(
            discord.ui.Button(
                label='Github', url='https://github.com/bryanforbes/Erasmus'
            )
        )


def get_about_embed(bot: Erasmus) -> Embed:
    total_members = 0
    total_unique = len(bot.users)

    text = 0
    voice = 0
    guilds = 0
    for guild in bot.guilds:
        guilds += 1

        if guild.unavailable or guild.member_count is None:
            continue

        total_members += guild.member_count
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                text += 1
            elif isinstance(channel, discord.VoiceChannel):
                voice += 1

    dpy_version = metadata.distribution('discord.py').version

    return Embed(
        fields=[
            {'name': 'Guilds', 'value': str(guilds)},
            {
                'name': 'Members',
                'value': f'{total_members} total\n{total_unique} unique',
            },
            {
                'name': 'Channels',
                'value': f'{text + voice} total\n{text} text\n{voice} voice',
            },
        ],
        footer={
            'text': f'Made with discord.py v{dpy_version}',
            'icon_url': 'http://i.imgur.com/5BFecvA.png',
        },
        timestamp=discord.utils.utcnow(),
    )


class Misc(Cog[Erasmus]):
    @commands.hybrid_command()
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: commands.Context[Erasmus], /) -> None:
        '''Get a link to invite Erasmus to your server'''

        await utils.send(ctx, view=InviteView(self.bot.application_id))

    @commands.hybrid_command()
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    async def about(self, ctx: commands.Context[Erasmus], /) -> None:
        '''Get info about Erasmus'''

        await utils.send(
            ctx,
            embeds=[get_about_embed(self.bot)],
            view=AboutView(self.bot.application_id),
        )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))
