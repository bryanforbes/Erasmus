from typing import List, Optional

from .mixins import Hashable
from .abc import GuildChannel
from .channel import VoiceChannel, TextChannel
from .member import Member
from .voice_client import VoiceClient
from .role import Role


class Guild(Hashable):
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
