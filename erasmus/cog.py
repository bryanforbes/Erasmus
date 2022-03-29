from __future__ import annotations

from botus_receptus.cog import Cog

from .erasmus import Erasmus


class ErasmusCog(Cog):
    bot: Erasmus

    def __init__(self, bot: Erasmus, /) -> None:
        self.bot = bot
