from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .data import VerseRange
    from .protocols import Bible


class ErasmusError(Exception):
    pass


class DoNotUnderstandError(ErasmusError):
    pass


class BibleNotSupportedError(ErasmusError):
    version: str

    def __init__(self, version: str) -> None:
        self.version = version


class BookNotUnderstoodError(ErasmusError):
    book: str

    def __init__(self, book: str) -> None:
        self.book = book


class BookNotInVersionError(ErasmusError):
    book: str
    version: str

    def __init__(self, book: str, version: str) -> None:
        self.book = book
        self.version = version


class ReferenceNotUnderstoodError(ErasmusError):
    reference: str

    def __init__(self, reference: str) -> None:
        self.reference = reference


class ServiceNotSupportedError(ErasmusError):
    service_name: str

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name


class ServiceTimeout(ErasmusError):
    bible: Bible

    def __init__(self, bible: Bible) -> None:
        self.bible = bible


class ServiceLookupTimeout(ServiceTimeout):
    verses: VerseRange

    def __init__(self, bible: Bible, verses: VerseRange) -> None:
        super().__init__(bible)
        self.verses = verses


class ServiceSearchTimeout(ServiceTimeout):
    terms: List[str]

    def __init__(self, bible: Bible, terms: List[str]) -> None:
        super().__init__(bible)
        self.terms = terms


class NoUserVersionError(ErasmusError):
    pass


class InvalidVersionError(ErasmusError):
    version: str

    def __init__(self, version: str) -> None:
        self.version = version


class InvalidConfessionError(ErasmusError):
    confession: str

    def __init__(self, confession: str) -> None:
        self.confession = confession


class NoSectionError(ErasmusError):
    confession: str
    section: str

    def __init__(self, confession: str, section: str, section_type: str) -> None:
        self.confession = confession
        self.section = section
        self.section_type = section_type


class NoSectionsError(ErasmusError):
    confession: str
    section_type: str

    def __init__(self, confession: str, section_type: str) -> None:
        self.confession = confession
        self.section_type = section_type
