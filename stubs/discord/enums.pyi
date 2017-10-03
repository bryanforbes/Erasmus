from enum import Enum, IntEnum


class ChannelType(Enum):
    text: int
    private: int
    voice: int
    group: int
    category: int


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


class VerificationLevel(IntEnum):
    none: int
    low: int
    medium: int
    high: int
    table_flip: int
    extreme: int
    double_table_flip: int


class ContentFilter(IntEnum):
    disabled: int
    no_role: int
    all_members: int


class Status(Enum):
    online: str
    offline: str
    idle: str
    dnd: str
    do_not_disturb: str
    invisible: str


class DefaultAvatar(Enum):
    blurple: int
    grey: int
    gray: int
    green: int
    orange: int
    red: int


class RelationshipType(Enum):
    friend: int
    blocked: int
    incoming_request: int
    outgoing_request: int


class AuditLogActionCategory(Enum):
    create: int
    delete: int
    update: int


class AuditLogAction(Enum):
    guild_update: int
    channel_create: int
    channel_update: int
    channel_delete: int
    overwrite_create: int
    overwrite_update: int
    overwrite_delete: int
    kick: int
    member_prune: int
    ban: int
    unban: int
    member_update: int
    member_role_update: int
    role_create: int
    role_update: int
    role_delete: int
    invite_create: int
    invite_update: int
    invite_delete: int
    webhook_create: int
    webhook_update: int
    webhook_delete: int
    emoji_create: int
    emoji_update: int
    emoji_delete: int
    message_delete: int

    @property
    def category(self) -> AuditLogActionCategory: ...

    @property
    def target_type(self) -> str: ...


class UserFlags(Enum):
    staff: int
    partner: int
    hypesquad: int
