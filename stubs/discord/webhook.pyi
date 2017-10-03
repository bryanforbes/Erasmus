from typing import Optional, Dict, Any, List
from aiohttp import ClientSession
from asyncio import AbstractEventLoop
from datetime import datetime
from .user import User
from .guild import Guild
from .channel import TextChannel
from .file import File
from .embeds import Embed
from .message import Message


class WebhookAdapter:
    webhook: 'Webhook'

    def request(self, verb: str, url: str, payload: Optional[Dict[str, Any]] = ...,
                multipart: Optional[Dict[str, str]] = ...) -> Any: ...

    def delete_webhook(self) -> Any: ...

    def edit_webhook(self, **payload) -> Any: ...

    def handle_execution_response(self, data: Any, *, wait: bool) -> Any: ...

    def execute_webhook(self, *, payload: Dict[str, Any], wait: bool = ..., file: str = ...) -> Any: ...


class AsyncWebhookAdapter(WebhookAdapter):
    session: ClientSession
    loop: AbstractEventLoop

    def __init__(self, session: ClientSession) -> None: ...

    async def request(self, verb: str, url: str, payload: Optional[Dict[str, Any]] = ...,
                      multipart: Optional[Dict[str, str]] = ...) -> Any: ...

    async def handle_execution_response(self, data: Any, *, wait: bool) -> Any: ...


class RequestsWebhookAdapter(WebhookAdapter):
    ...


class Webhook:
    id: int
    token: str
    guild_id: Optional[int]
    channel_id: Optional[int]
    user: Optional[User]
    name: Optional[str]
    avatar: Optional[str]

    def __init__(self, data: Dict[str, Any], *, adapter: WebhookAdapter, state: Optional[Any] = ...) -> None: ...

    @property
    def url(self) -> str: ...

    @classmethod
    def partial(cls, id: int, token: str, *, adapter: WebhookAdapter) -> 'Webhook': ...

    @classmethod
    def from_url(cls, url: str, *, adapter: WebhookAdapter) -> 'Webhook': ...

    @classmethod
    def from_state(cls, data: Dict[str, Any], state: Any) -> 'Webhook': ...

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def channel(self) -> Optional[TextChannel]: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def avatar_url(self) -> str: ...

    def avatar_url_as(self, *, format: Optional[str] = ..., size: int = ...) -> str: ...

    def delete(self) -> Any: ...

    def edit(self, **kwargs) -> Any: ...

    def send(self, content: Optional[str] = ..., *, wait: bool = ..., username: Optional[str] = ...,
             avatar_url: Optional[str] = ..., tts: bool = ..., file: Optional[File] = ..., embed: Optional[Embed] = ...,
             embeds: Optional[List[Embed]] = ...) -> Optional[Message]: ...

    def execute(self, *args, **kwargs) -> Any: ...
