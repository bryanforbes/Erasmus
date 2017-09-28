from enum import Enum


class MessageType(Enum):
    default: int
    recipient_add: int
    recipient_remove: int
    call: int
    channel_name_change: int
    channel_icon_change: int
    pins_add: int
    new_member: int


class VoiceRegion(Enum):
    us_west: str
    us_east: str
    us_south: str
    us_central: str
    eu_west: str
    eu_central: str
    singapore: str
    london: str
    sydney: str
    amsterdam: str
    frankfurt: str
    brazil: str
    vip_us_east: str
    vip_us_west: str
    vip_amsterdam: str


class Status(Enum):
    online: str
    offline: str
    idle: str
    dnd: str
    do_not_disturb: str
    invisible: str


class UserFlags(Enum):
    staff: int
    partner: int
    hypesquad: int
