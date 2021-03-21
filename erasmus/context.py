from __future__ import annotations

from typing import TYPE_CHECKING, Final

import discord
from botus_receptus import EmbedContext

from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus

_truncation_warning: Final = '**The passage was too long and has been truncated:**\n\n'
_max_length: Final = 2048 - (len(_truncation_warning) + 1)


class Context(EmbedContext):
    bot: Erasmus

    async def send_error(self, text: str, /) -> discord.Message:
        return await self.send_embed(text, color=discord.Color.red())

    async def send_passage(self, passage: Passage, /) -> discord.Message:
        text = passage.text

        if len(text) > 2048:
            text = f'{_truncation_warning}{text[:_max_length]}\u2026'

        embed = discord.Embed.from_dict(
            {'description': text, 'footer': {'text': passage.citation}}
        )

        return await self.send(embed=embed)
