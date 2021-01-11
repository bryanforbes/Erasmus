from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

import aiohttp
import async_timeout
from attr import attrib, dataclass

from . import services
from .config import Config
from .data import Passage, SearchResults, VerseRange
from .exceptions import ServiceLookupTimeout, ServiceSearchTimeout
from .protocols import Bible, Service

log = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceManager(object):
    session: aiohttp.ClientSession
    service_map: Dict[str, Service] = attrib(factory=dict)

    def __contains__(self, key: str) -> bool:
        return key in self.service_map

    def __len__(self) -> int:
        return self.service_map.__len__()

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        service = self.service_map.get(bible.service)
        assert service is not None
        try:
            log.debug(f'Getting passage {verses} ({bible.abbr})')
            with async_timeout.timeout(10):
                passage = await service.get_passage(self.session, bible, verses)
                passage.version = bible.abbr
                log.debug(f'Got passage {passage.citation}')
                return passage
        except asyncio.TimeoutError:
            raise ServiceLookupTimeout(bible, verses)

    async def search(
        self, bible: Bible, terms: List[str], *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        service = self.service_map.get(bible.service)
        assert service is not None
        try:
            with async_timeout.timeout(10):
                return await service.search(
                    self.session, bible, terms, limit=limit, offset=offset
                )
        except asyncio.TimeoutError:
            raise ServiceSearchTimeout(bible, terms)

    @classmethod
    def from_config(
        cls, config: Config, session: aiohttp.ClientSession
    ) -> ServiceManager:
        service_map: Dict[str, Service] = {}
        service_configs = config.get('services', {})

        for name, service_cls in services.__dict__.items():
            if callable(service_cls):
                section = service_configs.get(name)
                service_map[name] = service_cls(config=section)

        return cls(session, service_map)
