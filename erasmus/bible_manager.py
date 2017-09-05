from typing import Dict, List, Tuple
from collections import OrderedDict

from .config import ConfigObject
from .data import Passage, SearchResults
from .service import Service
from .exceptions import BibleNotSupportedError, ServiceNotSupportedError
from . import services


class Bible(object):
    __slots__ = ('name', 'service', 'version')

    name: str
    service: Service
    version: str

    def __init__(self, name: str, service: Service, version: str) -> None:
        self.name = name
        self.service = service
        self.version = version

    async def get_passage(self, passage: Passage) -> str:
        return await self.service.get_passage(self.version, passage)

    async def search(self, terms: List[str]) -> SearchResults:
        return await self.service.search(self.version, terms)


class BibleManager:
    config: ConfigObject
    bible_map: Dict[str, Bible]

    def __init__(self, config: ConfigObject) -> None:
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
        sorted_items = sorted(self.bible_map.items(), key=lambda item: item[0])
        return [(key, bible.name) for key, bible in sorted_items]

    # TODO: Book parsing should go here and then pass it to services for
    # service-specific modifications
    async def get_passage(self, version: str, passage: Passage) -> str:
        bible = self._get_bible(version)
        return await bible.get_passage(passage)

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        bible = self._get_bible(version)
        return await bible.search(terms)

    def _get_bible(self, version: str) -> Bible:
        bible = self.bible_map.get(version, None)

        if bible is None:
            raise BibleNotSupportedError(version)

        return bible
