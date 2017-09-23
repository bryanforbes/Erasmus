from typing import Dict, List, Tuple
from collections import OrderedDict

from .json import JSONObject
from .data import VerseRange, Passage, SearchResults
from .service import Service
from .exceptions import BibleNotSupportedError, ServiceNotSupportedError
from . import services


class Bible(object):
    __slots__ = ('name', 'abbr', 'service', 'service_version')

    name: str
    abbr: str
    service: Service
    service_version: str

    def __init__(self, *, name: str, abbr: str, service: Service, service_version: str, **kwargs) -> None:
        self.name = name
        self.abbr = abbr
        self.service = service
        self.service_version = service_version

    async def get_passage(self, verses: VerseRange) -> Passage:
        passage = await self.service.get_passage(self.service_version, verses)
        passage.version = self.abbr
        return passage

    async def search(self, terms: List[str]) -> SearchResults:
        return await self.service.search(self.service_version, terms)


class BibleManager:
    config: JSONObject
    bible_map: Dict[str, Bible]

    def __init__(self, config: JSONObject) -> None:
        self.config = config

        service_map = {}

        for key, config in config.services.items():
            service_map[key] = services.__dict__.get(key)(config)

        self.bible_map = OrderedDict()

        for key, bible_config in self.config.bibles.items():
            service = service_map.get(bible_config.service, None)

            if service is None:
                raise ServiceNotSupportedError(bible_config.service)

            bible_config.service = service
            self.bible_map[key] = Bible(**bible_config)

    def get_versions(self) -> List[Tuple[str, str]]:
        sorted_items = sorted(self.bible_map.items(), key=lambda item: item[0])
        return [(key, bible.name) for key, bible in sorted_items]

    async def get_passage(self, version: str, verses: VerseRange) -> Passage:
        bible = self._get_bible(version)
        return await bible.get_passage(verses)

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        bible = self._get_bible(version)
        return await bible.search(terms)

    def _get_bible(self, version: str) -> Bible:
        bible = self.bible_map.get(version, None)

        if bible is None:
            raise BibleNotSupportedError(version)

        return bible
