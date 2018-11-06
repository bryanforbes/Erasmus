from typing import TYPE_CHECKING
from botus_receptus import db, EmbedContext

import discord

from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus  # noqa

truncation_warning = '**The passage was too long and has been truncated:**\n\n'
max_length = 2048 - (len(truncation_warning) + 1)


class Context(db.Context, EmbedContext):
    bot: 'Erasmus'

    async def send_error(self, text: str) -> discord.Message:
        return await self.send_embed(text, color=discord.Color.red())

    async def send_passage(self, passage: Passage) -> discord.Message:
        text = passage.text

        if len(text) > 2048:
            text = f'{truncation_warning}{text[:max_length]}\u2026'

        embed = discord.Embed.from_data(
            {'description': text, 'footer': {'text': passage.citation}}
        )

        return await self.send(embed=embed)
