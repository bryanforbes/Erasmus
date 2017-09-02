from typing import (
    Any, Callable, Dict, Optional, Iterator, Coroutine,
    Union, Awaitable, Type
)


class Command:
    def __init__(self, name: str,
                 callback: Union[
                     Coroutine[Any, Any, Any],
                     Callable[..., Awaitable[Any]]],
                 **kwargs) -> None: ...


class GroupMixin:
    commands: Dict[str, Command]

    def recursively_remove_all_commands(self) -> None: ...

    def add_command(self, command: Command) -> None: ...

    def remove_command(self, name: str) -> Optional[Command]: ...

    def walk_commands(self) -> Iterator[Command]: ...

    def get_command(self, name: str) -> Optional[Command]: ...


def command(name: str = None, cls: Type[Command] = Command,
            **kwargs) -> Callable[..., Command]: ...
