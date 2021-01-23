from codecs import CodecInfo
from collections.abc import Iterable, Iterator
from logging import Logger
from re import Pattern
from typing import Any, AnyStr, ClassVar, Final, Generic, Literal, overload

def chardet_dammit(s: Any) -> str | None: ...

xml_encoding: Final[str]
html_meta: Final[str]
encoding_res: Final[dict[type[Any], dict[str, Pattern[Any]]]]

class EntitySubstitution:
    CHARACTER_TO_HTML_ENTITY: ClassVar[dict[str, str]]
    HTML_ENTITY_TO_CHARACTER: ClassVar[dict[str, str]]
    CHARACTER_TO_HTML_ENTITY_RE: ClassVar[Pattern[Any]]
    CHARACTER_TO_XML_ENTITY: ClassVar[dict[str, str]]
    BARE_AMPERSAND_OR_BRACKET: ClassVar[Pattern[Any]]
    AMPERSAND_OR_BRACKET: ClassVar[Pattern[Any]]
    @classmethod
    def quoted_attribute_value(cls, value: str) -> str: ...
    @classmethod
    def substitute_xml(cls, value: str, make_quoted_attribute: bool = ...) -> str: ...
    @classmethod
    def substitute_xml_containing_entities(
        cls, value: str, make_quoted_attribute: bool = ...
    ) -> str: ...
    @classmethod
    def substitute_html(cls, s: str) -> str: ...

class EncodingDetector(Generic[AnyStr]):
    markup: AnyStr
    sniffed_encoding: str | None
    override_encodings: Iterable[str]
    exclude_encodings: Iterable[str]
    chardet_encoding: str | None
    is_html: bool
    declared_encoding: str | None
    def __init__(
        self,
        markup: AnyStr,
        override_encodings: Iterable[str] = ...,
        is_html: bool = ...,
        exclude_encodings: Iterable[str] = ...,
    ) -> None: ...
    @property
    def encodings(self) -> Iterator[str]: ...
    @overload
    @classmethod
    def strip_byte_order_mark(cls, data: str) -> tuple[str, None]: ...
    @overload
    @classmethod
    def strip_byte_order_mark(cls, data: bytes) -> tuple[bytes, str | None]: ...
    @overload
    @classmethod
    def strip_byte_order_mark(
        cls, data: str | bytes
    ) -> tuple[str | bytes, str | None]: ...
    @classmethod
    def find_declared_encoding(
        cls,
        markup: str | bytes,
        is_html: bool = ...,
        search_entire_document: bool = ...,
    ) -> str | None: ...

class UnicodeDammit(Generic[AnyStr]):
    CHARSET_ALIASES: ClassVar[dict[str, str]]
    ENCODINGS_WITH_SMART_QUOTES: ClassVar[list[str]]
    smart_quotes_to: Literal['ascii', 'html', 'xml'] | None
    tried_encodings: list[tuple[str, Literal['strict', 'replace']]]
    contains_replacement_characters: bool
    is_html: bool
    log: Logger
    detector: EncodingDetector[AnyStr]
    markup: AnyStr
    unicode_markup: str | None
    original_encoding: str | None
    def __init__(
        self,
        markup: AnyStr,
        override_encodings: Iterable[str] = ...,
        smart_quotes_to: Literal['ascii', 'html', 'xml'] | None = ...,
        is_html: bool = ...,
        exclude_encodings: Iterable[str] = ...,
    ) -> None: ...
    @property
    def declared_html_encoding(self) -> str | None: ...
    def find_codec(self, charset: str) -> CodecInfo | None: ...
    MS_CHARS: ClassVar[dict[bytes, str | tuple[str, str]]]
    MS_CHARS_TO_ASCII: ClassVar[dict[bytes, str | tuple[str, str]]]
    WINDOWS_1252_TO_UTF8: ClassVar[dict[int, bytes]]
    MULTIBYTE_MARKERS_AND_SIZES: ClassVar[list[tuple[int, int, int]]]
    FIRST_MULTIBYTE_MARKER: ClassVar[int]
    LAST_MULTIBYTE_MARKER: ClassVar[int]
    @classmethod
    def detwingle(
        cls, in_bytes: AnyStr, main_encoding: str = ..., embedded_encoding: str = ...
    ) -> str | bytes: ...
