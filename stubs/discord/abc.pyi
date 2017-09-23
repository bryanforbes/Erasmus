from typing import List, Union, Iterator
from datetime import datetime

from .message import Message
from .role import Role
from .permissions import PermissionOverwrite, Permissions
from .context_managers import Typing
from .voice_client import VoiceClient
from .member import Member
from .embeds import Embed


class Snowflake:
    @property
    def created_at(self) -> datetime: ...


class User:
    @property
    def display_name(self) -> str: ...

    @property
    def mention(self) -> str: ...


class PrivateChannel:
    ...


class GuildChannel:
    @property
    def changed_roles(self) -> List[Role]: ...

    @property
    def mention(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...

    def overwrites_for(self, obj: Union[User, Role]) -> PermissionOverwrite: ...

    @property
    def overwrites(self) -> PermissionOverwrite: ...

    def permissions_for(self, member: Member) -> Permissions: ...

    async def delete(self, *, reason: str = None) -> None: ...


class Messageable:
    async def send(self, content: str = None, *, tts: bool = False, embed: Embed = None,
                   file: object = None, files: List[object] = None, delete_after: float = None,
                   nonce: int = None) -> Message: ...

    async def trigger_typing(self) -> None: ...

    def typing(self) -> Typing: ...

    async def get_message(self, id: int) -> Message: ...

    async def pins(self) -> List[Message]: ...

    def history(self, *, limit: int = 100, before: Union[Message, datetime] = None,
                after: Union[Message, datetime] = None, around: Union[Message, datetime] = None,
                reverse: bool = None) -> Iterator[Message]: ...


class Connectable:
    async def connect(self, *, timeout: float = 60.0, reconnect: bool = True) -> VoiceClient: ...
