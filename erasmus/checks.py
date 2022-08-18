from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from discord import app_commands

if TYPE_CHECKING:
    from collections.abc import Callable

    import discord
    from botus_receptus.types import Coroutine
    from discord.ext import commands

_T = TypeVar('_T')


def is_owner() -> Callable[[_T], _T]:
    def predicate(interaction: discord.Interaction, /) -> Coroutine[bool]:
        return cast('commands.Bot', interaction.client).is_owner(interaction.user)

    return app_commands.check(predicate)
