from __future__ import annotations

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


def setup(bot: Erasmus) -> None:
    bot.add_cog(Misc(bot))
