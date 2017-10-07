from typing import Dict, List
from configparser import ConfigParser

from .data import VerseRange, Passage, SearchResults, Bible
from .service import Service
from . import services


class ServiceManager(object):
    __slots__ = ('service_map')

    service_map: Dict[str, Service]

    def __init__(self, config: ConfigParser) -> None:
        self.service_map = {}

        config_sections = config.sections()

        for name, cls in services.__dict__.items():
            if callable(cls):
                section_name = f'services:{name}'
                section = None

                if section_name in config_sections:
                    section = config[section_name]

                self.service_map[name] = cls(section)

    def __contains__(self, key: str) -> bool:
        return self.service_map.__contains__(key)

    def __len__(self) -> int:
        return self.service_map.__len__()

    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        service = self.service_map.get(bible['service'])
        passage = await service.get_passage(bible, verses)
        passage.version = bible['abbr']
        return passage

    async def search(self, bible: Bible, terms: List[str]) -> SearchResults:
        service = self.service_map.get(bible['service'])
        return await service.search(bible, terms)
