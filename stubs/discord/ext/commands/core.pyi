from typing import (
    Any, Callable, Dict, Optional, Iterator, Coroutine,
    Union, Awaitable, Type, ValuesView, List
)

CallbackType = Union[
    Coroutine[Any, Any, Any],
    Callable[..., Awaitable[Any]]]


class Command:
    name: str
    callback: CallbackType
    help: str
    brief: str
    usage: str
    aliases: List[str]
    enabled: bool

    def __init__(self, name: str, callback: CallbackType, **kwargs) -> None: ...


class GroupMixin:
    all_commands: Dict[str, Command]

    @property
    def commands(self) -> ValuesView[Command]: ...

    def recursively_remove_all_commands(self) -> None: ...

    def add_command(self, command: Command) -> None: ...

    def remove_command(self, name: str) -> Optional[Command]: ...

    def walk_commands(self) -> Iterator[Command]: ...

    def get_command(self, name: str) -> Optional[Command]: ...

    def command(self, *args, **kwargs) -> Callable[..., Command]: ...

    def group(self, *args, **kwargs) -> Callable[..., Command]: ...


def command(name: Optional[str] = ..., cls: Optional[Type[Command]] = ..., **kwargs) -> Callable[..., Command]: ...
