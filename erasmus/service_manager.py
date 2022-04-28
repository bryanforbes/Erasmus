from __future__ import annotations

import asyncio
import logging
from typing import Final

import aiohttp
import async_timeout
from attrs import define, field

from . import services
from .config import Config
from .data import Passage, SearchResults, VerseRange
from .exceptions import (
    ServiceLookupTimeout,
    ServiceNotSupportedError,
    ServiceSearchTimeout,
)
from .types import Bible, Service

_log: Final = logging.getLogger(__name__)


@define
class ServiceManager(object):
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
                passage.version = bible.abbr
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
        cls,
        config: Config,
        session: aiohttp.ClientSession,
        /,
    ) -> ServiceManager:
        service_map: dict[str, Service] = {}
        service_configs = config.get('services', {})

        for name, service_cls in services.__dict__.items():
            if callable(service_cls):
                section = service_configs.get(name)
                service_map[name] = service_cls(config=section, session=session)

        return cls(service_map)
