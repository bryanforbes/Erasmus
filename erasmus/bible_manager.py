from typing import Dict, List, Tuple
from collections import OrderedDict
from importlib import import_module

from .config import ConfigObject
from .service import Service, Passage
from .exceptions import BibleNotSupportedError, ServiceNotSupportedError
from . import services

class Bible(object):
    __slots__ = ('name', 'service', 'version')

    name: str
    service: Service
    version: str

    def __init__(self, name: str, service: Service, version: str):
        self.name = name
        self.service = service
        self.version = version

    async def get_passage(self, passage: Passage) -> str:
        return await self.service.get_passage(self.version, passage)

class BibleManager:
    config: ConfigObject
    bible_map: Dict[str, Bible]

    def __init__(self, config: ConfigObject):
        self.config = config

        service_map = {}

        for key, config in config.services.items():
            service_map[key] = services.__dict__.get(key)(config)

        self.bible_map = OrderedDict()

        for key, bible_config in self.config.bibles.items():
            service = service_map.get(bible_config.service, None)

            if service is None:
                raise ServiceNotSupportedError(bible_config.service)

            self.bible_map[key] = Bible(
                bible_config.name,
                service,
                bible_config.service_version
            )

    def get_versions(self) -> List[Tuple[str, str]]:
        return [
            (key, bible.name) for key, bible in sorted(self.bible_map.items(), key=lambda item: item[0])
        ]

    # TODO: Verse parsing to a known format (specifically book name) should probably go here and
    # then pass it to services for service-specific modifications
    async def get_passage(self, version: str, book: str, chapter: int, verse_start: int, verse_end: int = -1) -> str:
        bible = self.bible_map.get(version, None)

        if bible is None:
            raise BibleNotSupportedError(version)

        passage = Passage(book, chapter, verse_start, verse_end)
        return await bible.get_passage(passage)
