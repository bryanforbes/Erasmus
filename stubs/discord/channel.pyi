from .abc import Messageable, GuildChannel, Connectable
from .mixins import Hashable


class TextChannel(Messageable, GuildChannel, Hashable):
    ...


class VoiceChannel(Connectable, GuildChannel, Hashable):
    ...


class DMChannel(Messageable, Hashable):
    ...


class GroupChannel(Messageable, Hashable):
    ...
