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


class Status(Enum):
    online: str
    offline: str
    idle: str
    dnd: str
    do_not_disturb: str
    invisible: str
