from __future__ import annotations

from typing import TYPE_CHECKING

from .cog import Bible

if TYPE_CHECKING:
    from ...erasmus import Erasmus

__all__ = ('Bible',)


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Bible(bot))
