from typing import Any, Hashable
from .abc import GuildChannel
from .colour import Colour
from .message import Message
from .role import Role
from .permissions import Permissions
from .channel import VoiceChannel
from .user import User


class VoiceState:
    deaf: bool
    mute: bool
    self_mute: bool
    self_deaf: bool
    afk: bool
    channel: VoiceChannel


class Member(User, Hashable):
    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...

    @property
    def colour(self) -> Colour: ...

    color = colour

    def mentioned_in(self, message: Message) -> bool: ...

    def permissions_in(self, channel: GuildChannel) -> bool: ...

    @property
    def top_role(self) -> Role: ...

    @property
    def guild_permissions(self) -> Permissions: ...

    @property
    def voice(self) -> VoiceState: ...
