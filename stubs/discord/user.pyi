from typing import Optional, NamedTuple, List, Any, Hashable
from .abc import User as _BaseUser, Messageable, GuildChannel
from .channel import DMChannel
from .enums import UserFlags
from .permissions import Permissions
from .message import Message
from datetime import datetime


class Profile(NamedTuple):
    flags: UserFlags
    user: 'User'
    mutual_guilds: List[int]
    connected_accounts: List[Any]
    premium_since: Optional[datetime]

    @property
    def nitro(self) -> bool: ...

    premium: bool

    @property
    def staff(self) -> bool: ...

    @property
    def hypesquad(self) -> bool: ...

    @property
    def partner(self) -> bool: ...


class BaseUser(_BaseUser, Hashable):
    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', '_state')

    name: str
    id: str
    discriminator: str
    avatar: Optional[str]
    bot: bool

    @property
    def avatar_url(self) -> str: ...

    def is_avatar_animated(self) -> bool: ...

    def avatar_url_as(self, *, format: Optional[str] = ..., static_format: str = ...,
                      size: int = ...) -> str: ...

    @property
    def default_avatar(self) -> str: ...

    @property
    def default_avatar_url(self) -> str: ...

    @property
    def mention(self) -> str: ...

    def permissions_in(self, channel: GuildChannel) -> Permissions: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def display_name(self) -> str: ...

    def mentioned_in(self, message: Message) -> bool: ...


class ClientUser(BaseUser):
    verified: bool
    email: Optional[str]
    mfa_enabled: bool
    premium: bool


class User(BaseUser, Messageable):
    @property
    def dm_channel(self) -> Optional[DMChannel]: ...

    async def create_dm(self) -> DMChannel: ...

    def is_friend(self) -> bool: ...

    def is_blocked(self) -> bool: ...

    async def block(self) -> None: ...

    async def unblock(self) -> None: ...

    async def remove_friend(self) -> None: ...

    async def send_friend_request(self) -> None: ...
