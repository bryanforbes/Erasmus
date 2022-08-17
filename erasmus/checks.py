from __future__ import annotations

from typing import TYPE_CHECKING, cast

from discord import app_commands

if TYPE_CHECKING:
    import discord
    from discord.ext import commands

    from .types import Coroutine


def is_owner():
    def predicate(interaction: discord.Interaction, /) -> Coroutine[bool]:
        return cast('commands.Bot', interaction.client).is_owner(interaction.user)

    return app_commands.check(predicate)
