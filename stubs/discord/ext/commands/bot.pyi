from typing import Callable, Union, Awaitable
from .core import GroupMixin
from ...client import Client, Message

CommandPrefix = Union[
    str,
    Callable[['Bot', Message], Union[str, Awaitable[str]]]]


class Bot(GroupMixin, Client):
    def __init__(self, command_prefix: CommandPrefix, **options) -> None: ...

    async def type(self) -> None: ...

    async def say(self, content: str = None, *, tts: bool = False,
                  embed: object = None) -> Message: ...

    async def process_commands(self, message: Message) -> None: ...
