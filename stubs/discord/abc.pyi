from typing import List, Union, Iterator, Optional, Tuple, Dict
from datetime import datetime
from abc import ABCMeta

from .message import Message
from .role import Role
from .permissions import PermissionOverwrite, Permissions
from .context_managers import Typing
from .voice_client import VoiceClient
from .member import Member
from .embeds import Embed
from .channel import CategoryChannel
from .invite import Invite
from .user import ClientUser
from .guild import Guild


class Snowflake(metaclass=ABCMeta):
    id: int

    @property
    def created_at(self) -> datetime: ...


class User(metaclass=ABCMeta):
    name: str
    discriminator: str
    avatar: Optional[str]
    bot: bool

    @property
    def display_name(self) -> str: ...

    @property
    def mention(self) -> str: ...


class PrivateChannel(metaclass=ABCMeta):
    me: ClientUser


class GuildChannel:
    name: str
    guild: Guild
    position: int

    @property
    def changed_roles(self) -> List[Role]: ...

    @property
    def mention(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...

    def overwrites_for(self, obj: Union[User, Role]) -> PermissionOverwrite: ...

    @property
    def overwrites(self) -> List[Tuple[Union[Role, Member], PermissionOverwrite]]: ...

    @property
    def category(self) -> Optional[CategoryChannel]: ...

    def permissions_for(self, member: Member) -> Permissions: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...

    async def set_permissions(self, target: Union[Member, Role], *, overwrite: Optional[PermissionOverwrite] = ...,
                              reason: Optional[str] = ..., **permissions: Dict[str, Optional[bool]]) -> None: ...

    async def create_invite(self, *, reason: Optional[str] = ..., max_age: int = ..., max_uses: int = ...,
                            temporary: bool = ..., unique: bool = ...) -> Invite: ...

    async def invites(self) -> List[Invite]: ...


class Messageable(metaclass=ABCMeta):
    async def send(self, content: Optional[str] = ..., *, tts: bool = ..., embed: Optional[Embed] = ...,
                   file: Optional[object] = ..., files: Optional[List[object]] = ...,
                   delete_after: Optional[float] = ..., nonce: Optional[int] = ...) -> Message: ...

    async def trigger_typing(self) -> None: ...

    def typing(self) -> Typing: ...

    async def get_message(self, id: int) -> Message: ...

    async def pins(self) -> List[Message]: ...

    def history(self, *, limit: int = ..., before: Optional[Union[Message, datetime]] = ...,
                after: Optional[Union[Message, datetime]] = ..., around: Optional[Union[Message, datetime]] = ...,
                reverse: Optional[bool] = ...) -> Iterator[Message]: ...


class Connectable(metaclass=ABCMeta):
    async def connect(self, *, timeout: float = ..., reconnect: bool = ...) -> VoiceClient: ...
