from __future__ import annotations

from typing import TYPE_CHECKING, cast

from discord import app_commands

if TYPE_CHECKING:
    from collections.abc import Callable

    import discord
    from botus_receptus.types import Coroutine
    from discord.ext import commands


def is_owner[T]() -> Callable[[T], T]:
    def predicate(itx: discord.Interaction, /) -> Coroutine[bool]:
        return cast('commands.Bot', itx.client).is_owner(itx.user)

    return app_commands.check(predicate)
