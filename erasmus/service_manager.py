from typing import Dict, List

from .json import JSONObject
from .data import VerseRange, Passage, SearchResults
from .service import Service
from . import services


class Bible(object):
    __slots__ = ('command', 'name', 'abbr', 'service', 'service_version')

    command: str
    name: str
    abbr: str
    service: str
    service_version: str


class ServiceManager(object):
    __slots__ = ('service_map')

    service_map: Dict[str, Service]

    def __init__(self, config: JSONObject) -> None:
        self.service_map = {}

        for name, cls in services.__dict__.items():
            if callable(cls):
                service_config = config.services.get(name, {})
                self.service_map[name] = cls(service_config)

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        service = self.service_map.get(bible.service)
        passage = await service.get_passage(bible.service_version, verses)
        passage.version = bible.abbr
        return passage

    async def search(self, bible: Bible, terms: List[str]) -> SearchResults:
        service = self.service_map.get(bible.service)
        return await service.search(bible.service_version, terms)
