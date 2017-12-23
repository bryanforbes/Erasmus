from typing import Union, Callable, Awaitable, TypeVar, Optional, List, NamedTuple
from asyncio import AbstractEventLoop
from .user import User, ClientUser
from .game import Game
from .enums import Status
from .guild import Guild
from .emoji import Emoji
from .abc import PrivateChannel, GuildChannel
from .voice_client import VoiceClient

_Type = TypeVar('_Type')
_ReturnType = TypeVar('_ReturnType')
_CoroType = Callable[..., Awaitable[_Type]]


class AppInfo(NamedTuple):
    id: int
    name: str
    description: str
    icon: str
    owner: User

    @property
    def icon_url(self) -> str: ...


class Client:
    user: User
    loop: AbstractEventLoop

    @property
    def latency(self) -> float: ...

    @property
    def user(self) -> Optional[ClientUser]: ...

    @property
    def guilds(self) -> List[Guild]: ...

    @property
    def emojis(self) -> List[Emoji]: ...

    @property
    def private_channels(self) -> List[PrivateChannel]: ...

    @property
    def voice_client(self) -> List[VoiceClient]: ...

    def is_ready(self) -> bool: ...

    async def on_error(self, event_method, *args, **kwargs) -> None: ...

    async def login(self, token: str, *, bot: bool = ...) -> None: ...

    async def logout(self) -> None: ...

    async def connect(self, *, reconnect: bool = ...) -> None: ...

    async def close(self) -> None: ...

    def clear(self) -> None: ...

    async def start(self, token: str, *, bot: bool = ..., reconnect: bool = ...) -> None: ...

    def run(self, token: str, *, bot: bool = ..., reconnect: bool = ...) -> None: ...

    def is_closed(self) -> bool: ...

    @property
    def users(self) -> List[User]: ...

    def get_channel(self, id: int) -> Optional[Union[GuildChannel, PrivateChannel]]: ...

    def get_guild(self, id: int) -> Optional[Guild]: ...

    def get_user(self, id: int) -> Optional[User]: ...

    def get_emoji(self, id: int) -> Optional[Emoji]: ...

    def event(self, coro: _CoroType[_ReturnType]) -> _CoroType[_ReturnType]: ...

    def async_event(self, coro: Union[Callable[..., _ReturnType],
                                      _CoroType[_ReturnType]]) -> _CoroType[_ReturnType]: ...

    async def change_presence(self, *, game: Optional[Game] = ..., status: Optional[Status] = ...,
                              afk: bool = ...) -> None: ...
