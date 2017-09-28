from typing import Optional
from .abc import Messageable, GuildChannel, Connectable
from .mixins import Hashable


class TextChannel(Messageable, GuildChannel, Hashable):
    id: int
    category_id: int
    topic: Optional[str]

    def is_nsfw(self) -> bool: ...


class VoiceChannel(Connectable, GuildChannel, Hashable):
    ...


class CategoryChannel(GuildChannel, Hashable):
    ...


class DMChannel(Messageable, Hashable):
    ...


class GroupChannel(Messageable, Hashable):
    ...
