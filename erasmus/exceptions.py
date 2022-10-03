from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enum import Enum

    from .data import Book, VerseRange
    from .types import Bible


class ErasmusError(Exception):
    pass


class DoNotUnderstandError(ErasmusError):
    pass


class BibleNotSupportedError(ErasmusError):
    version: str

    def __init__(self, version: str, /) -> None:
        self.version = version


class BookNotUnderstoodError(ErasmusError):
    book: str

    def __init__(self, book: str, /) -> None:
        self.book = book


class BookNotInVersionError(ErasmusError):
    book: str
    version: str

    def __init__(self, book: str, version: str, /) -> None:
        self.book = book
        self.version = version


class BookMappingInvalid(ErasmusError):
    version: str
    from_book: Book
    to_osis: str

    def __init__(self, version: str, from_book: Book, to_osis: str, /) -> None:
        self.version = version
        self.from_book = from_book
        self.to_osis = to_osis


class ReferenceNotUnderstoodError(ErasmusError):
    reference: str

    def __init__(self, reference: str, /) -> None:
        self.reference = reference


class ServiceNotSupportedError(ErasmusError):
    bible: Bible

    def __init__(self, bible: Bible, /) -> None:
        self.bible = bible


class ServiceTimeout(ErasmusError):
    bible: Bible

    def __init__(self, bible: Bible, /) -> None:
        self.bible = bible


class ServiceLookupTimeout(ServiceTimeout):
    verses: VerseRange

    def __init__(self, bible: Bible, verses: VerseRange, /) -> None:
        super().__init__(bible)
        self.verses = verses


class ServiceSearchTimeout(ServiceTimeout):
    terms: list[str]

    def __init__(self, bible: Bible, terms: list[str], /) -> None:
        super().__init__(bible)
        self.terms = terms


class NoUserVersionError(ErasmusError):
    pass


class InvalidVersionError(ErasmusError):
    version: str

    def __init__(self, version: str, /) -> None:
        self.version = version


class InvalidTimeError(ErasmusError):
    time: str

    def __init__(self, time: str, /) -> None:
        self.time = time


class InvalidTimeZoneError(ErasmusError):
    timezone: str

    def __init__(self, timezone: str, /) -> None:
        self.timezone = timezone


class DailyBreadNotInVersionError(ErasmusError):
    version: str

    def __init__(self, version: str, /) -> None:
        self.version = version


class InvalidConfessionError(ErasmusError):
    confession: str

    def __init__(self, confession: str, /) -> None:
        self.confession = confession


class NoSectionError(ErasmusError):
    confession: str
    section: str
    section_type: str

    def __init__(self, confession: str, section: str, section_type: Enum, /) -> None:
        self.confession = confession
        self.section = section
        self.section_type = section_type.value
