class DoNotUnderstandError(Exception):
    pass


class BibleNotSupportedError(Exception):
    version: str

    def __init__(self, version: str) -> None:
        self.version = version


class BookNotUnderstoodError(Exception):
    book: str

    def __init__(self, book: str) -> None:
        self.book = book


class ServiceNotSupportedError(Exception):
    service_name: str

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
