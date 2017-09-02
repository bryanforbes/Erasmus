class DoNotUnderstandError(Exception):
    pass


class BibleNotSupportedError(Exception):
    version: str

    def __init__(self, version: str) -> None:
        self.version = version


class ServiceNotSupportedError(Exception):
    service_name: str

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
