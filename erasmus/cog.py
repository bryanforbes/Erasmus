from typing import TYPE_CHECKING

from discord.ext import commands

from .context import Context

if TYPE_CHECKING:
    Cog = commands.Cog[Context]
else:
    Cog = commands.Cog
