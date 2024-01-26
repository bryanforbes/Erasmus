from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ...erasmus import Erasmus
    from ...l10n import GroupLocalizer, Localizer
    from ...service_manager import ServiceManager


class _BaseParent(Protocol):
    @property
    def bot(self) -> Erasmus: ...


class ParentCog(_BaseParent, Protocol):
    @property
    def localizer(self) -> Localizer: ...

    @property
    def service_manager(self) -> ServiceManager: ...


class ParentGroup(_BaseParent, Protocol):
    @property
    def localizer(self) -> GroupLocalizer: ...
