from typing import List, Optional, AsyncContextManager, Awaitable, Generator, Any, TYPE_CHECKING
import attr
from asyncpg import Connection
import discord
from discord.ext import commands
from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus  # noqa

truncation_warning = '**The passage was too long and has been truncated:**\n\n'
max_length = 2048 - (len(truncation_warning) + 1)


@attr.s(slots=True, auto_attribs=True)
class AquireContextManager(AsyncContextManager[Connection], Awaitable[Connection]):
    ctx: 'Context'
    timeout: Optional[float] = None

    def __await__(self) -> Generator[Any, None, Connection]:
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self) -> Connection:
        return await self.ctx._acquire(self.timeout)

    async def __aexit__(self, *args: Any) -> None:
        await self.ctx.release()


class Context(commands.Context):
    bot: 'Erasmus'
    db: Connection

    async def send_embed(self, text: Optional[str] = None, *, embed: Optional[discord.Embed] = None) -> discord.Message:
        if text is not None:
            if embed is None:
                embed = discord.Embed()
            embed.description = text

        return await self.send(embed=embed)

    async def send_pages(self, paginator: commands.Paginator, *,
                         embed: Optional[discord.Embed] = None) -> List[discord.Message]:
        messages: List[discord.Message] = []

        for page in paginator.pages:
            messages.append(await self.send_embed(page, embed=embed))
            embed = None

        return messages

    async def send_error(self, text: Optional[str] = None, *, embed: Optional[discord.Embed] = None) -> discord.Message:
        if embed is not None:
            embed = discord.Embed.from_data(embed.to_dict())
        else:
            embed = discord.Embed()

        embed.color = discord.Color.red()

        return await self.send_embed(text, embed=embed)

    async def send_passage(self, passage: Passage) -> discord.Message:
        text = passage.text

        if len(text) > 2048:
            text = f'{truncation_warning}{text[:max_length]}\u2026'

        embed = discord.Embed.from_data({
            'description': text,
            'footer': {
                'text': passage.citation
            }
        })

        return await self.send(embed=embed)

    async def _acquire(self, timeout: Optional[float]) -> Connection:
        if not hasattr(self, 'db'):
            self.db = await self.bot.pool.acquire(timeout=timeout)

        return self.db

    def acquire(self, *, timeout: Optional[float] = None) -> AquireContextManager:
        return AquireContextManager(self, timeout)

    async def release(self) -> None:
        if hasattr(self, 'db'):
            await self.bot.pool.release(self.db)
            del self.db
