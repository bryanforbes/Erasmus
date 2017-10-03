from typing import Optional
from .mixins import Hashable
from .guild import Guild
from .user import User
from .abc import GuildChannel
from datetime import datetime


class Invite(Hashable):
    max_age: int
    code: str
    guild: Guild
    revoked: bool
    created_at: datetime
    temporary: bool
    uses: int
    max_uses: int
    inviter: User
    channel: GuildChannel

    @property
    def id(self) -> str: ...

    @property
    def url(self) -> str: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...
