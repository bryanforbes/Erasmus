from __future__ import annotations

from typing import Dict, List, cast, Any
import attr
import aiohttp

from .data import VerseRange, Passage, SearchResults
from .service import Service
from .config import Config
from . import services
from .db.bible import BibleVersion


@attr.s(slots=True, auto_attribs=True)
class ServiceManager(object):
    session: aiohttp.ClientSession
    service_map: Dict[str, Service[Any]] = attr.ib(default=attr.Factory(dict))

    def __contains__(self, key: str) -> bool:
        return self.service_map.__contains__(key)

    def __len__(self) -> int:
        return self.service_map.__len__()

    async def get_passage(self, bible: BibleVersion, verses: VerseRange) -> Passage:
        service = cast(Service[Any], self.service_map.get(bible.service))
        passage = await service.get_passage(bible, verses)
        passage.version = bible.abbr
        return passage

    async def search(self, bible: BibleVersion, terms: List[str]) -> SearchResults:
        service = cast(Service[Any], self.service_map.get(bible.service))
        return await service.search(bible, terms)

    @classmethod
    def from_config(
        cls, config: Config, session: aiohttp.ClientSession
    ) -> ServiceManager:  # noqa: F821
        service_map: Dict[str, Service[Any]] = {}
        service_configs = config.get('services', {})

        for name, service_cls in services.__dict__.items():
            if callable(service_cls):
                section = service_configs.get(name)
                service_map[name] = service_cls(section, session)

        return cls(session, service_map)
