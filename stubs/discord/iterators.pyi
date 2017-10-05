from typing import AsyncIterator as TypingAsyncIterator, TypeVar, Any, List, Optional, Union
from datetime import datetime
from .user import User
from .message import Message
from .emoji import Emoji
from .abc import Messageable
from .guild import Guild
from .audit_logs import AuditLogEntry
from .abc import Snowflake
from .enums import AuditLogAction

_T = TypeVar('_T')


class _AsyncIterator(TypingAsyncIterator[_T]):
    def get(self, **attrs: Any) -> _T: ...

    async def find(self, predicate: Any) -> _T: ...

    def map(self, func: Any) -> '_MappedAsyncIterator'[_T]: ...

    def filter(self, predicate: Any) -> '_FilteredAsyncIterator'[_T]: ...

    async def flatten(self) -> List[_T]: ...


class _MappedAsyncIterator(_AsyncIterator[_T]):
    async def next(self) -> _T: ...


class _FilteredAsyncIterator(_AsyncIterator[_T]):
    async def next(self) -> _T: ...


class ReactionIterator(_AsyncIterator[User]):
    def __init__(self, message: Message, emoji: Emoji, limit: int = ..., after: Optional[Any] = ...) -> None: ...

    async def next(self) -> User: ...

    async def fill_users(self) -> None: ...


class HistoryIterator(_AsyncIterator[Message]):
    def __init__(self, messageable: Messageable, limit: int, before: Optional[Union[Message, datetime]] = ...,
                 after: Optional[Union[Message, datetime]] = ...,
                 around: Optional[Union[Message, datetime]] = ...,
                 reverse: Optional[bool] = ...) -> None: ...

    async def next(self) -> Message: ...

    async def fill_messages(self) -> None: ...


class AuditLogIterator(_AsyncIterator[AuditLogEntry]):
    def __init__(self, guild: Guild, limit: Optional[int] = ...,
                 before: Optional[Union[Snowflake, datetime]] = ...,
                 after: Optional[Union[Snowflake, datetime]] = ...,
                 reverse: Optional[bool] = ...,
                 user_id: Optional[Snowflake] = ...,
                 action_type: Optional[AuditLogAction] = ...) -> None: ...

    async def next(self) -> AuditLogEntry: ...
