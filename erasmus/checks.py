from __future__ import annotations

from typing import TYPE_CHECKING, cast

from discord import app_commands

if TYPE_CHECKING:
    import discord
    from discord.ext import commands


def is_owner():
    async def predicate(interaction: discord.Interaction, /) -> bool:
        return await cast('commands.Bot', interaction.client).is_owner(interaction.user)

    return app_commands.check(predicate)
