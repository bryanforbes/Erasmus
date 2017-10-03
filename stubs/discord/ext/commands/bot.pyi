from typing import Callable, Union, Awaitable, List, Any, Optional, Dict, Type
from .core import GroupMixin
from .context import Context
import discord

CommandPrefix = Union[
    str,
    Callable[['Bot', discord.Message], Union[str, Awaitable[str]]]]


def when_mentioned(bot: 'Bot', msg: discord.Message) -> str: ...


def when_mentioned_or(*prefixes) -> Callable[['Bot', discord.Message], List[str]]: ...


class BotBase(GroupMixin):
    command_prefix: CommandPrefix
    description: str
    self_bot: bool
    pm_help: Optional[bool]
    help_attrs: Dict[str, Any]
    command_not_found: str
    command_has_no_subcommands: str
    owner_id: Optional[int]

    def __init__(self, command_prefix: CommandPrefix, **options) -> None: ...

    async def get_context(self, message: discord.Message, *, cls: Type[Context] = ...) -> Context: ...

    async def invoke(self, ctx: Context) -> None: ...

    async def process_commands(self, message: discord.Message) -> None: ...

    async def on_message(self, message: discord.Message) -> None: ...

    def add_cog(self, cog: Any) -> None: ...


class Bot(BotBase, discord.Client):
    ...


class AutoShardedBot(BotBase, discord.AutoShardedClient):
    ...
