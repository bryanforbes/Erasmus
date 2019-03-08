from __future__ import annotations

from typing import Dict, List
from attr import dataclass, attrib
import aiohttp

from .data import VerseRange, Passage, SearchResults
from .config import Config
from . import services
from .protocols import Bible, Service


@dataclass(slots=True)
class ServiceManager(object):
    session: aiohttp.ClientSession
    service_map: Dict[str, Service] = attrib(factory=dict)

    def __contains__(self, key: str) -> bool:
        return self.service_map.__contains__(key)

    def __len__(self) -> int:
        return self.service_map.__len__()

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        service = self.service_map.get(bible.service)
        assert service is not None
        passage = await service.get_passage(bible, verses)
        passage.version = bible.abbr
        return passage

    async def search(
        self, bible: Bible, terms: List[str], *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        service = self.service_map.get(bible.service)
        assert service is not None
        return await service.search(bible, terms, limit=limit, offset=offset)

    @classmethod
    def from_config(
        cls, config: Config, session: aiohttp.ClientSession
    ) -> ServiceManager:
        service_map: Dict[str, Service] = {}
        service_configs = config.get('services', {})

        for name, service_cls in services.__dict__.items():
            if callable(service_cls):
                section = service_configs.get(name)
                service_map[name] = service_cls(config=section, session=session)

        return cls(session, service_map)
