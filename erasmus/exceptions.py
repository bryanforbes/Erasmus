from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .data import Bible, VerseRange  # noqa: F401


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


class ServiceTimeout(Exception):
    bible: 'Bible'

    def __init__(self, bible: 'Bible') -> None:
        self.bible = bible


class ServiceLookupTimeout(ServiceTimeout):
    verses: 'VerseRange'

    def __init__(self, bible: 'Bible', verses: 'VerseRange') -> None:
        super().__init__(bible)
        self.verses = verses


class ServiceSearchTimeout(ServiceTimeout):
    terms: List[str]

    def __init__(self, bible: 'Bible', terms: List[str]) -> None:
        super().__init__(bible)
        self.terms = terms


class NoUserVersionError(Exception):
    pass


class InvalidVersionError(Exception):
    version: str

    def __init__(self, version: str) -> None:
        self.version = version


class InvalidConfessionError(Exception):
    confession: str

    def __init__(self, confession: str) -> None:
        self.confession = confession


class NoSectionError(Exception):
    confession: str
    section: str

    def __init__(self, confession: str, section: str, section_type: str) -> None:
        self.confession = confession
        self.section = section
        self.section_type = section_type


class NoSectionsError(Exception):
    confession: str
    section_type: str

    def __init__(self, confession: str, section_type: str) -> None:
        self.confession = confession
        self.section_type = section_type
