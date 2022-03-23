from __future__ import annotations

import discord
from botus_receptus import Cog, formatting
from discord.ext import commands

from ..context import Context
from ..erasmus import Erasmus


class Misc(Cog):
    def __init__(self, bot: Erasmus, /) -> None:
        self.bot = bot

    @commands.command(brief='Get the invite link for Erasmus')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: Context, /) -> None:
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
        await ctx.send(
            f'<{discord.utils.oauth_url("349394562336292876", permissions=perms)}>'
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def stats(self, ctx: Context, /) -> None:
        await ctx.send(
            formatting.code_block(
                f'''Servers: {len(self.bot.guilds)}
Users: {len(self.bot.users)}'''
            )
        )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))
