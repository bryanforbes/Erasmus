from typing import Any, Iterable, Tuple, Generic, TypeVar, Optional, Hashable

PT = TypeVar('PT')


class _BasePermission(Generic[PT], Iterable[Tuple[str, PT]]):
    create_instant_invite: PT
    kick_members: PT
    ban_members: PT
    administrator: PT
    manage_channels: PT
    manage_guild: PT
    add_reactions: PT
    view_audit_log: PT
    read_messages: PT
    send_messages: PT
    send_tts_messages: PT
    manage_messages: PT
    embed_links: PT
    attach_files: PT
    read_message_history: PT
    mention_everyone: PT
    external_emojis: PT
    connect: PT
    speak: PT
    mute_members: PT
    deafen_members: PT
    move_members: PT
    use_voice_activation: PT
    change_nickname: PT
    manage_nickname: PT
    manage_roles: PT
    manage_webhooks: PT
    manage_emojis: PT


class Permissions(_BasePermission[bool], Hashable):
    def __init__(self, permissions: int = 0) -> None: ...

    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...

    def __le__(self, other: Any) -> bool: ...

    def __ge__(self, other: Any) -> bool: ...

    def __lt__(self, other: Any) -> bool: ...

    def __gt__(self, other: Any) -> bool: ...

    def is_subset(self, other: Any) -> bool: ...

    def is_superset(self, other: Any) -> bool: ...

    def is_strict_subset(self, other: Any) -> bool: ...

    def is_strict_superset(self, other: Any) -> bool: ...

    @classmethod
    def none(cls) -> 'Permissions': ...

    @classmethod
    def all(cls) -> 'Permissions': ...

    @classmethod
    def all_channel(cls) -> 'Permissions': ...

    @classmethod
    def general(cls) -> 'Permissions': ...

    @classmethod
    def text(cls) -> 'Permissions': ...

    @classmethod
    def voice(cls) -> 'Permissions': ...

    def update(self, **kwargs) -> None: ...


class PermissionOverwrite(_BasePermission[Optional[bool]]):
    def __init__(self, **kwargs) -> None: ...

    def pair(self) -> Tuple[Permissions, Permissions]: ...

    @classmethod
    def from_pair(cls, allow: Permissions, deny: Permissions) -> 'PermissionOverwrite': ...

    def is_empty(self) -> bool: ...

    def update(self, **kwargs) -> None: ...
