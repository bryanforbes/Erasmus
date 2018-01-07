from typing import NamedTuple, Optional, List
from datetime import datetime
from .mixins import Hashable
from .role import Role
from .guild import Guild


class PartialEmoji(NamedTuple):
    animated: bool
    name: str
    id: Optional[int]

    def is_custom_emoji(self) -> bool: ...

    def is_unicode_emoji(self) -> bool: ...

    @property
    def url(self) -> Optional[str]: ...


class Emoji(Hashable):
    name: str
    id: int
    require_colons: bool
    animated: bool
    managed: bool
    guild_id: int

    @property
    def created_at(self) -> datetime: ...

    @property
    def url(self) -> str: ...

    @property
    def roles(self) -> List[Role]: ...

    @property
    def guild(self) -> Guild: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...

    async def edit(self, *, name: str, reason: Optional[str] = ...) -> None: ...
