from typing import Optional, List, Union
from datetime import datetime
from .guild import Guild
from .channel import TextChannel, DMChannel, GroupChannel
from .enums import MessageType
from .member import Member
from .user import User
from .embeds import Embed


class Attachment:
    ...


class Message:
    tts: bool
    type: MessageType
    author: Union[Member, User]
    content: str
    embeds: List[Embed]
    channel: Union[TextChannel, DMChannel, GroupChannel]
    mention_everyone: bool
    mentions: List[Member]
    id: int
    webhook_id: Optional[int]
    attachments: List[Attachment]
    pinned: bool
    reactions: List[object]

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def raw_mentions(self) -> List[int]: ...

    @property
    def raw_channel_mentions(self) -> List[int]: ...

    @property
    def raw_role_mentions(self) -> List[int]: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def edited_at(self) -> Optional[datetime]: ...

    @property
    def system_content(self) -> str: ...

    async def delete(self) -> None: ...

    async def edit(self, *, content: Optional[str], embed: Optional[Embed], delete_after: Optional[float]) -> None: ...

    async def pin(self) -> None: ...

    async def unpin(self) -> None: ...
