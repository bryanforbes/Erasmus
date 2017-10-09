from discord.ext import commands


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


class BookNotInVersionError(Exception):
    book: str
    version: str

    def __init__(self, book: str, version: str) -> None:
        self.book = book
        self.version = version


class ReferenceNotUnderstoodError(Exception):
    reference: str

    def __init__(self, reference: str) -> None:
        self.reference = reference


class ServiceNotSupportedError(Exception):
    service_name: str

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name


class OnlyDirectMessage(commands.CheckFailure):
    pass
