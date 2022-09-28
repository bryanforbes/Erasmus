from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Final, TypeGuard

import async_timeout
from attrs import define, field

from . import services
from .exceptions import (
    ServiceLookupTimeout,
    ServiceNotSupportedError,
    ServiceSearchTimeout,
)

if TYPE_CHECKING:
    import aiohttp

    from .config import Config
    from .data import Passage, SearchResults, VerseRange
    from .services.base_service import BaseService
    from .types import Bible, Service

_log: Final = logging.getLogger(__name__)


def _is_service_cls(obj: Any, /) -> TypeGuard[type[BaseService]]:
    return hasattr(obj, 'from_config') and callable(obj.from_config)


@define(frozen=True)
class ServiceManager:
    service_map: dict[str, Service] = field(factory=dict)
    timeout: float = 10

    def __contains__(self, key: str, /) -> bool:
        return key in self.service_map

    def __len__(self, /) -> int:
        return len(self.service_map)

    async def get_passage(self, bible: Bible, verses: VerseRange, /) -> Passage:
        service = self.service_map.get(bible.service)

        if service is None:
            raise ServiceNotSupportedError(bible)

        try:
            _log.debug(f'Getting passage {verses} ({bible.abbr})')
            async with async_timeout.timeout(self.timeout):
                passage = await service.get_passage(bible, verses)
                _log.debug(f'Got passage {passage.citation}')
                return passage
        except asyncio.TimeoutError as e:
            raise ServiceLookupTimeout(bible, verses) from e

    async def search(
        self, bible: Bible, terms: list[str], /, *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        service = self.service_map.get(bible.service)
        assert service is not None
        try:
            async with async_timeout.timeout(self.timeout):
                return await service.search(bible, terms, limit=limit, offset=offset)
        except asyncio.TimeoutError as e:
            raise ServiceSearchTimeout(bible, terms) from e

    @classmethod
    def from_config(
        cls, config: Config, session: aiohttp.ClientSession, /
    ) -> ServiceManager:
        service_configs = config.get('services', {})

        return cls(
            {
                name: service_cls.from_config(service_configs.get(name), session)
                for name, service_cls in services.__dict__.items()
                if _is_service_cls(service_cls)
            }
        )
