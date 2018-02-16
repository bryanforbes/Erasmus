from typing import NamedTuple, Callable, Any, Optional, Dict, ClassVar
from asyncio import Future
import threading
from .client import Client
from .game import Game
from .enums import Status


class ResumeWebSocket(Exception):
    shard_id: int

    def __init__(self, shard_id: int) -> None: ...


class EventListener(NamedTuple):
    predicate: Callable[..., bool]
    event: str
    result: Optional[Callable[..., Any]]
    future: Future[Any]


class KeepAliveHandler(threading.Thread):
    def run(self) -> None: ...

    def get_payload(self) -> Dict[str, Any]: ...

    def stop(self) -> None: ...

    def ack(self) -> None: ...


class VoiceKeepAliveHandler(KeepAliveHandler):
    def get_payload(self) -> Dict[str, Any]: ...


class DiscordWebSocket:
    DISPATCH: ClassVar[int]
    HEARTBEAT: ClassVar[int]
    IDENTIFY: ClassVar[int]
    PRESENCE: ClassVar[int]
    VOICE_STATE: ClassVar[int]
    VOICE_PING: ClassVar[int]
    RESUME: ClassVar[int]
    RECONNECT: ClassVar[int]
    REQUEST_MEMBERS: ClassVar[int]
    INVALIDATE_SESSION: ClassVar[int]
    HELLO: ClassVar[int]
    HEARTBEAT_ACK: ClassVar[int]
    GUILD_SYNC: ClassVar[int]

    @classmethod
    async def from_client(cls, client: Client, *, shard_id: Optional[int] = ..., session: Optional[int] = ...,
                          sequence: Optional[int] = ..., resume: bool = ...) -> 'DiscordWebSocket': ...

    def wait_for(self, event: str, predicate: Callable[..., bool],
                 result: Optional[Callable[..., Any]] = ...) -> Future[Any]: ...

    async def identify(self) -> None: ...

    async def resume(self) -> None: ...

    async def received_message(self, msg: str) -> None: ...

    @property
    def latency(self) -> float: ...

    async def poll_event(self) -> None: ...

    async def send(self, data: str) -> None: ...

    async def send_as_json(self, data: Any) -> None: ...

    async def change_presence(self, *, game: Game=None, status: Status=None, afk: bool=None) -> None: ...

    async def close_connection(self, *args, **kwargs) -> None: ...


class DiscordVoiceWebSocket:
    IDENTIFY: ClassVar[int]
    SELECT_PROTOCOL: ClassVar[int]
    READY: ClassVar[int]
    HEARTBEAT: ClassVar[int]
    SESSION_DESCRIPTION: ClassVar[int]
    SPEAKING: ClassVar[int]
    HEARTBEAT_ACK: ClassVar[int]
    RESUME: ClassVar[int]
    HELLO: ClassVar[int]
    INVALIDATE_SESSION: ClassVar[int]

    async def send_as_json(self, data: Any) -> None: ...

    async def resume(self) -> None: ...

    async def identify(self) -> None: ...

    @classmethod
    async def from_client(cls, client: Client, *, resume: bool = ...) -> 'DiscordVoiceWebSocket': ...

    async def select_protocol(self, ip: str, port: str) -> None: ...

    async def speak(self, is_speaking: bool = ...) -> None: ...

    async def received_message(self, msg: str) -> None: ...

    async def initial_connection(self, data: Dict[str, Any]) -> None: ...

    async def load_secret_key(self, data: Dict[str, Any]) -> None: ...

    async def poll_event(self) -> None: ...

    async def close_connection(self, *args, **kwargs) -> None: ...
