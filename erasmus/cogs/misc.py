from __future__ import annotations

from botus_receptus.formatting import code_block
from discord.ext import commands

from ..context import Context
from ..erasmus import Erasmus


class Misc(commands.Cog[Context]):
    def __init__(self, bot: Erasmus) -> None:
        self.bot = bot

    @commands.command(brief='Get the invite link for Erasmus')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def invite(self, ctx: Context) -> None:
        await ctx.send(
            '<https://discordapp.com/oauth2/authorize?client_id='
            '349394562336292876&scope=bot&permissions=388160>'
        )

    @commands.command(hidden=True)
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def areyoumyfriend(self, ctx: Context) -> None:
        if ctx.author.id in {547579430164365313, 139178723235594240}:
            await ctx.send(f'No, I am not your friend, {ctx.author.mention}')
        elif ctx.author.id == 275782127168126977:
            await ctx.send(f'You are on my permanent troll list, {ctx.author.mention}')
        else:
            await ctx.send(f"Of course I'm your friend, {ctx.author.mention}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def stats(self, ctx: Context) -> None:
        await ctx.send(
            code_block(
                f'''Servers: {len(self.bot.guilds)}
Users: {len(self.bot.users)}'''
            )
        )


def setup(bot: Erasmus) -> None:
    bot.add_cog(Misc(bot))
