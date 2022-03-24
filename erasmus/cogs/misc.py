from __future__ import annotations

import discord
from botus_receptus import Cog, formatting
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from discord.ext import commands

from ..context import Context
from ..erasmus import Erasmus


class InviteView(discord.ui.View):
    def __init__(self, application_id: int, /, *, timeout: float | None = 180) -> None:
        super().__init__(timeout=timeout)

        perms = discord.Permissions(
            add_reactions=True,
            attach_files=True,
            embed_links=True,
            manage_messages=True,
            manage_threads=True,
            read_message_history=True,
            read_messages=True,
            send_messages=True,
            send_messages_in_threads=True,
            use_external_emojis=True,
        )

        self.add_item(
            discord.ui.Button(
                label='Invite Erasmus',
                url=discord.utils.oauth_url(application_id, permissions=perms),
            )
        )


class MiscBase(Cog):
    bot: Erasmus

    def __init__(self, bot: Erasmus, /) -> None:
        self.bot = bot


class Misc(MiscBase):
    @commands.command(brief='Get the invite link for Erasmus')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: Context, /) -> None:
        await ctx.send(view=InviteView(self.bot.application_id), reference=ctx.message)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def stats(self, ctx: Context, /) -> None:
        await ctx.send(
            formatting.code_block(
                f'''Servers: {len(self.bot.guilds)}
Users: {len(self.bot.users)}'''
            )
        )


class MiscAppCommands(MiscBase):
    @app_commands.command()
    async def invite(self, interaction: discord.Interaction, /) -> None:
        '''Get a link to invite the bot to your server'''
        await interaction.response.send_message(
            view=InviteView(self.bot.application_id)
        )

    @app_commands.command()
    @admin_guild_only()
    async def stats(self, interaction: discord.Interaction, /) -> None:
        '''Show stats about Erasmus'''
        await interaction.response.send_message(
            formatting.code_block(
                f'''Servers: {len(self.bot.guilds)}
Users: {len(self.bot.users)}'''
            )
        )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))
    await bot.add_cog(MiscAppCommands(bot))
