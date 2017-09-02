from typing import Coroutine, Any, Union, Callable
from .message import Message
from .user import User


class Client:
    user: User

    async def on_error(self, event_method, *args, **kwargs) -> None: ...

    async def login(self, token_or_email: str, password: str = None, *,
                    bot: bool = True) -> None: ...

    async def logout(self) -> None: ...

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def start(self, token_or_email: str, password: str = None, *,
                    bot: bool = None) -> None: ...

    async def run(self, token_or_email: str, password: str = None, *,
                  bot: bool = None) -> None: ...

    async def send_message(self, destination: object, content: Any = None,
                           *, tts: bool = False,
                           embed: object = None) -> Message: ...

    @property
    def is_logged_in(self) -> bool: ...

    @property
    def is_closed(self) -> bool: ...

    def event(self,
              coro: Coroutine[Any, Any, Any]) -> Coroutine[Any, Any, Any]: ...

    def async_event(self,
                    coro: Union[
                        Callable[..., Any],
                        Coroutine[Any, Any, Any]
                    ]) -> Coroutine[Any, Any, Any]: ...
