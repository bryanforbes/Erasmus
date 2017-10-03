from typing import Iterable, Any, Sized, Union, Optional
from datetime import datetime
from . import enums
from .member import Member
from .user import User


class AuditLogDiff(Sized, Iterable[Any]):
    ...


class AuditLogChanges:
    before: AuditLogDiff
    after: AuditLogDiff


class AuditLogEntry:
    action: enums.AuditLogAction
    user: Union[Member, User]
    id: int
    target: Any
    reason: Optional[str]
    extra: Any

    @property
    def created_at(self) -> datetime: ...

    @property
    def category(self) -> enums.AuditLogActionCategory: ...

    @property
    def changes(self) -> AuditLogChanges: ...

    @property
    def before(self) -> AuditLogDiff: ...

    @property
    def after(self) -> AuditLogDiff: ...
