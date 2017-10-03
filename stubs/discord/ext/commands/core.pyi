from typing import Any, Callable, Dict, Optional, Iterator, Union, Awaitable, Type, ValuesView, List
from .context import Context
from .cooldowns import BucketType

CallbackType = Callable[..., Awaitable[Any]]
ErrorHandlerType = Callable[..., Awaitable[None]]


class Command:
    name: str
    callback: CallbackType
    help: str
    brief: str
    usage: str
    aliases: List[str]
    enabled: bool
    parent: Optional['Command']
    description: str
    hidden: bool

    def __init__(self, name: str, callback: CallbackType, **kwargs) -> None: ...

    def error(self, coro: ErrorHandlerType) -> ErrorHandlerType: ...

    def is_on_cooldown(self, ctx: Context) -> bool: ...

    def reset_cooldown(self, ctx: Context) -> None: ...


class GroupMixin:
    all_commands: Dict[str, Command]

    @property
    def commands(self) -> ValuesView[Command]: ...

    def recursively_remove_all_commands(self) -> None: ...

    def add_command(self, command: Command) -> None: ...

    def remove_command(self, name: str) -> Optional[Command]: ...

    def walk_commands(self) -> Iterator[Command]: ...

    def get_command(self, name: str) -> Optional[Command]: ...

    def command(self, *args, **kwargs) -> Callable[[CallbackType], Command]: ...

    def group(self, *args, **kwargs) -> Callable[..., Command]: ...


def command(name: Optional[str] = ..., cls: Optional[Type[Command]] = ..., **kwargs) -> Callable[..., Command]: ...


def check(predicate: Union[Callable[[Context], bool],
                           Callable[[Context], Awaitable[bool]]]): ...


def has_role(name: str): ...


def has_any_role(*names: str): ...


def has_permissions(**perms: bool): ...


def bot_has_role(*names: str): ...


def bot_has_permissions(**perms: bool): ...


def guild_only(): ...


def is_owner(): ...


def is_nsfw(): ...


def cooldown(rate: int, per: float, type: BucketType = ...): ...
