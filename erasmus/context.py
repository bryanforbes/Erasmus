from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from botus_receptus import EmbedContext

if TYPE_CHECKING:
    from botus_receptus.types import Coroutine

    from .erasmus import Erasmus  # noqa: F401


class Context(EmbedContext['Erasmus']):
    def send_error(self, text: str, /) -> Coroutine[discord.Message]:
        return self.send_embed(text, color=discord.Color.red(), reference=self.message)
