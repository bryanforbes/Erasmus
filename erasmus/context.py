from __future__ import annotations

from typing import TYPE_CHECKING
from botus_receptus import EmbedContext

import discord

from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus

truncation_warning = '**The passage was too long and has been truncated:**\n\n'
max_length = 2048 - (len(truncation_warning) + 1)


class Context(EmbedContext):
    bot: Erasmus

    async def send_error(self, text: str) -> discord.Message:
        return await self.send_embed(text, color=discord.Color.red())

    async def send_passage(self, passage: Passage) -> discord.Message:
        text = passage.text

        if len(text) > 2048:
            text = f'{truncation_warning}{text[:max_length]}\u2026'

        embed = discord.Embed.from_dict(
            {'description': text, 'footer': {'text': passage.citation}}
        )

        return await self.send(embed=embed)


class GuildContext(Context):
    guild: discord.Guild
