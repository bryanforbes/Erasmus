from __future__ import annotations

from typing import TYPE_CHECKING, Final

import discord
from botus_receptus import util
from discord.ext import commands

from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus


_truncation_warning: Final = '**The passage was too long and has been truncated:**\n\n'
_max_length: Final = 4096 - (len(_truncation_warning) + 1)


def _get_passage_text(passage: Passage, /) -> str:
    text = passage.text

    if len(text) > 6000:
        text = f'{_truncation_warning}{text[:_max_length]}\u2026'

    return text


async def send_context_passage(
    ctx: commands.Context[Erasmus],
    passage: Passage,
) -> discord.Message:
    return await util.send_context(
        ctx, description=_get_passage_text(passage), footer={'text': passage.citation}
    )


async def send_interaction_passage(
    interaction: discord.Interaction,
    passage: Passage,
    /,
    *,
    ephemeral: bool = False,
) -> None:
    await util.send_interaction(
        interaction,
        description=_get_passage_text(passage),
        footer={'text': passage.citation},
        ephemeral=ephemeral,
    )
