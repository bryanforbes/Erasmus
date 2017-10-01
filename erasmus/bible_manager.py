from typing import Dict, List, Tuple, Any
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

    def __init__(self, config: JSONObject, bibles: List[Any]) -> None:
        self.config = config

        service_map = {}

        for key, config in config.services.items():
            service_map[key] = services.__dict__.get(key)(config)

        self.bible_map = OrderedDict()

        for bible_version in sorted(bibles, key=lambda item: item.command):
            service = service_map.get(bible_version.service)

            if service is None:
                raise ServiceNotSupportedError(bible_version.service)

            self.bible_map[bible_version.command] = Bible(name=bible_version.name,
                                                          abbr=bible_version.abbr,
                                                          service=service,
                                                          service_version=bible_version.service_version)

    def __contains__(self, item: str) -> bool:
        return item in self.bible_map

    def get_versions(self) -> List[Tuple[str, str]]:
        return [(key, bible.name) for key, bible in self.bible_map.items()]

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
