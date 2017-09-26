from typing import Callable, Union, Awaitable, List, Any, Optional, Dict, Type, TypeVar
from .core import GroupMixin
from .context import Context
from ...client import Client
from ...message import Message
from ...shard import AutoShardedClient

CommandPrefix = Union[
    str,
    Callable[['Bot', Message], Union[str, Awaitable[str]]]]

ContextType = TypeVar('ContextType', covariant=True)


def when_mentioned(bot: 'Bot', msg: Message) -> str: ...


def when_mentioned_or(*prefixes) -> Callable[['Bot', Message], List[str]]: ...


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

    async def get_context(self, message: Message, *, cls: Type[Context] = Context) -> Context: ...

    async def invoke(self, ctx: Context) -> None: ...

    async def process_commands(self, message: Message) -> None: ...

    async def on_message(self, message: Message) -> None: ...


class Bot(BotBase, Client):
    ...


class AutoShardedBot(BotBase, AutoShardedClient):
    ...
