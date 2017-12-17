from typing import List, Optional, AsyncContextManager, Awaitable, Generator, Any, TYPE_CHECKING
from asyncpg import Connection
import discord
from discord.ext import commands
from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus  # noqa

truncation_warning = '**The passage was too long and has been truncated:**\n\n'
max_length = 2048 - (len(truncation_warning) + 1)


class AquireContextManager(AsyncContextManager[Connection], Awaitable[Connection]):
    __slots__ = ('ctx', 'timeout')

    ctx: 'Context'
    timeout: float

    def __init__(self, ctx: 'Context', timeout: Optional[float]) -> None:
        self.ctx = ctx
        self.timeout = timeout

    def __await__(self) -> Generator[Any, None, Connection]:
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self) -> Connection:
        return await self.ctx._acquire(self.timeout)

    async def __aexit__(self, *args) -> None:
        await self.ctx.release()


class Context(commands.Context):
    bot: 'Erasmus'
    db: Optional[Connection] = None

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

        return await self.send_to_author(embed=embed)

    async def send_error_to_author(self, text: str = None, *, embed: discord.Embed = None) -> discord.Message:
        if embed is not None:
            embed = discord.Embed.from_data(embed.to_dict())
        else:
            embed = discord.Embed()

        embed.color = discord.Color.red()

        return await self.send_to_author(text, embed=embed)

    async def send_to_author(self, text: str = None, *, embed: discord.Embed = None) -> discord.Message:
        if text is not None:
            if embed is None:
                embed = discord.Embed()
            embed.description = text

        mention = None  # type: str

        if not isinstance(self.message.channel, discord.DMChannel) and \
                not isinstance(self.message.channel, discord.GroupChannel):
            mention = self.author.mention

        return await self.send(mention, embed=embed)

    async def send_pages_to_author(self, pages: List[str], *, embed: discord.Embed = None) -> List[discord.Message]:
        messages = []

        for page in pages:
            messages.append(await self.send_to_author(page, embed=embed))
            embed = None

        return messages

    async def _acquire(self, timeout: Optional[float]) -> Connection:
        if self.db is None:
            self.db = await self.bot.pool.acquire(timeout=timeout)

        return self.db

    def acquire(self, *, timeout: Optional[float] = None) -> AquireContextManager:
        return AquireContextManager(self, timeout)

    async def release(self) -> None:
        if self.db is not None:
            await self.bot.pool.release(self.db)
            self.db = None
