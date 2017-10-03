from typing import List, Optional, Tuple, Dict, Union, NamedTuple, Set, Any
from datetime import datetime

from .mixins import Hashable
from .abc import GuildChannel, Snowflake
from .channel import VoiceChannel, TextChannel, CategoryChannel
from .member import Member
from .voice_client import VoiceClient
from .role import Role
from .emoji import Emoji
from .enums import VoiceRegion, VerificationLevel, ContentFilter, AuditLogAction
from .permissions import PermissionOverwrite
from .user import User
from .webhook import Webhook
from .invite import Invite
from .iterators import AuditLogIterator

VALID_ICON_FORMATS: Set[str] = ...


class BanEntry(NamedTuple):
    user: User
    reason: str


class Guild(Hashable):
    name: str
    roles: List[Role]
    emojis: Tuple[Emoji]
    region: VoiceRegion
    afk_timeout: int
    afk_channel: Optional[VoiceChannel]
    icon: str
    id: int
    owner_id: int
    unavailable: bool
    mfa_level: int
    verification_level: VerificationLevel
    explicit_content_filter: ContentFilter
    features: List[str]
    splash: str

    @property
    def channels(self) -> List[GuildChannel]: ...

    @property
    def large(self) -> bool: ...

    @property
    def voice_channels(self) -> List[VoiceChannel]: ...

    @property
    def me(self) -> Member: ...

    @property
    def voice_client(self) -> VoiceClient: ...

    @property
    def text_channels(self) -> List[TextChannel]: ...

    @property
    def categories(self) -> List[CategoryChannel]: ...

    def by_category(self) -> List[Tuple[Optional[CategoryChannel], List[GuildChannel]]]: ...

    def get_channel(self, channel_id: int) -> Optional[GuildChannel]: ...

    @property
    def system_channel(self) -> Optional[TextChannel]: ...

    @property
    def members(self) -> List[Member]: ...

    def get_member(self, user_id: int) -> Optional[Member]: ...

    @property
    def default_role(self) -> Role: ...

    @property
    def owner(self) -> Member: ...

    @property
    def icon_url(self) -> str: ...

    def icon_url_as(self, *, format: str = ..., size: int = ...) -> str: ...

    @property
    def splash_url(self) -> str: ...

    @property
    def member_count(self) -> int: ...

    @property
    def chunked(self) -> bool: ...

    @property
    def shard_id(self) -> Optional[int]: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def role_hierarchy(self) -> List[Role]: ...

    def get_member_named(self, name: str) -> Optional[Member]: ...

    async def create_text_channel(self, name: str, *,
                                  overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                  category: Optional[CategoryChannel] = ...,
                                  reason: Optional[str] = ...) -> TextChannel: ...

    async def create_voice_channel(self, name: str, *,
                                   overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                   category: Optional[CategoryChannel] = ...,
                                   reason: Optional[str] = ...) -> VoiceChannel: ...

    async def create_category(self, name: str, *,
                              overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                              reason: Optional[str] = ...) -> CategoryChannel: ...

    async def leave(self) -> None: ...

    async def delete(self) -> None: ...

    async def edit(self, *, reason: Optional[str] = ..., **fields) -> None: ...

    async def bans(self) -> List[BanEntry]: ...

    async def prune_members(self, *, days: int, reason: Optional[str] = ...) -> int: ...

    async def webhooks(self) -> List[Webhook]: ...

    async def estimate_pruned_members(self, *, days: int) -> int: ...

    async def invites(self) -> List[Invite]: ...

    async def create_custom_emoji(self, *, name: str, image: bytes, reason: Optional[str] = ...) -> Emoji: ...

    async def create_role(self, *, reason: Optional[str] = ..., **fields) -> Role: ...

    async def kick(self, user: Snowflake, *, reason: Optional[str] = ...) -> None: ...

    async def ban(self, user: Snowflake, *, reason: Optional[str] = ..., delete_message_days: int = ...) -> None: ...

    async def unban(self, user: Snowflake, *, reason: Optional[str] = ...) -> None: ...

    async def vanity_invite(self) -> Invite: ...

    def ack(self) -> Any: ...

    def audit_logs(self, *, limit: int = ..., before: Optional[Union[Snowflake, datetime]] = ...,
                   after: Optional[Union[Snowflake, datetime]] = ...,
                   reverse: Optional[bool] = ..., user: Optional[Snowflake] = ...,
                   action: Optional[AuditLogAction] = ...) -> AuditLogIterator: ...
