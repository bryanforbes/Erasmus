from typing import Any, Hashable, Optional, List, Union
from .abc import User as _BaseUser, Messageable, GuildChannel
from .activity import Activity, Game, Streaming, Spotify
from .enums import Status
from .colour import Colour
from .message import Message
from .role import Role
from .permissions import Permissions
from .channel import VoiceChannel
from datetime import datetime


class VoiceState:
    deaf: bool
    mute: bool
    self_mute: bool
    self_deaf: bool
    afk: bool
    channel: VoiceChannel


class Member(Messageable, _BaseUser, Hashable):
    roles: List[Role]
    joined_at: datetime
    status: Status
    activity: Union[Activity, Game, Streaming, Spotify]
    nick: Optional[str]

    # From BaseUser:
    name: str
    id: int
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
    # End From: BaseUser

    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...

    @property
    def colour(self) -> Colour: ...

    color = colour

    @property
    def top_role(self) -> Role: ...

    @property
    def guild_permissions(self) -> Permissions: ...

    @property
    def voice(self) -> VoiceState: ...
