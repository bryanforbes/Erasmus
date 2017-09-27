from typing import Optional, NamedTuple, List, Any
from .abc import User as _User, Messageable
from .channel import DMChannel
from .enums import UserFlags
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


class BaseUser(_User):
    name: str
    id: str
    discriminator: str
    avatar: Optional[str]
    bot: bool


class ClientUser(BaseUser):
    verified: bool
    email: Optional[str]
    mfa_enabled: bool
    premium: bool


class User(Messageable, BaseUser):
    @property
    def dm_channel(self) -> Optional[DMChannel]: ...

    async def create_dm(self) -> DMChannel: ...

    def is_friend(self) -> bool: ...

    def is_blocked(self) -> bool: ...

    async def block(self) -> None: ...

    async def unblock(self) -> None: ...

    async def remove_friend(self) -> None: ...

    async def send_friend_request(self) -> None: ...
