from typing import List, Optional
from datetime import datetime, timedelta
from .message import Message
from .user import User
from .channel import GroupChannel
from .enums import VoiceRegion
from .member import VoiceState


class CallMessage:
    message: Message
    participants: Optional[List[User]]
    ended_timestamp: Optional[datetime]

    def __init__(self, message: Message, *, ended_timestamp: Optional[datetime] = ...,
                 participants: Optional[List[User]] = ...) -> None: ...

    @property
    def call_ended(self) -> bool: ...

    @property
    def channel(self) -> GroupChannel: ...

    @property
    def duration(self) -> timedelta: ...


class GroupCall:
    call: Optional[CallMessage]
    unavailable: Optional[bool]
    ringing: List[User]
    region: VoiceRegion

    def __init__(self, **kwargs) -> None: ...

    @property
    def connected(self) -> List[User]: ...

    @property
    def channel(self) -> GroupChannel: ...

    def voice_state_for(self, user: User) -> Optional[VoiceState]: ...
