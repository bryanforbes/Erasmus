from typing import Any, Optional, Dict, Set
from .emoji import PartialEmoji


class RawMessageDeleteEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[Any]

    def __init__(self, data: Dict[str, Any]) -> None: ...


class RawBulkMessageDeleteEvent:
    message_ids: Set[int]
    channel_id: int
    guild_id: Optional[int]

    def __init__(self, data: Dict[str, Any]) -> None: ...


class RawMessageUpdateEvent:
    message_id: int
    data: Dict[str, Any]

    def __init__(self, data: Dict[str, Any]) -> None: ...


class RawReactionActionEvent:
    message_id: int
    channel_id: int
    user_id: int
    emoji: PartialEmoji
    guild_id: Optional[int]

    def __init__(self, data: Dict[str, Any], emoji: PartialEmoji) -> None: ...


class RawReactionClearEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[int]

    def __init__(self, data: Dict[str, Any]) -> None: ...
