from typing import Dict, List, Tuple
from collections import OrderedDict
from importlib import import_module

from .config import ConfigObject
from .services import Service
from .exceptions import BibleNotSupportedError, ServiceNotSupportedError

class Bible:
    name: str
    service: Service
    version: str

    def __init__(self, name: str, service: Service, version: str):
        self.name = name
        self.service = service
        self.version = version

    async def get_verse(self, *args, **kwargs) -> str:
        return await self.service.get_verse(self.version, *args, **kwargs)

class BibleManager:
    config: ConfigObject
    bible_map: Dict[str, Bible]

    def __init__(self, config: ConfigObject):
        self.config = config

        service_map = {}

        for key, config in config.services.items():
            service_map[key] = import_module('.services', __package__).__dict__.get(key)(config)

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
        return [ (key, bible.name) for key, bible in self.bible_map.items()]

    async def get_verse(self, version: str, *args) -> str:
        bible = self.bible_map.get(version, None)

        if bible is None:
            raise BibleNotSupportedError(version)

        return await bible.get_verse(*args)
