from codecs import CodecInfo
from logging import Logger
from typing import (
    Any,
    AnyStr,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Pattern,
    Tuple,
    Type,
    Union,
    overload,
)
from typing_extensions import Final, Literal

def chardet_dammit(s: Any) -> Optional[str]: ...

xml_encoding: Final[str]
html_meta: Final[str]
encoding_res: Final[Dict[Type[Any], Dict[str, Pattern[Any]]]]

class EntitySubstitution:
    CHARACTER_TO_HTML_ENTITY: ClassVar[Dict[str, str]]
    HTML_ENTITY_TO_CHARACTER: ClassVar[Dict[str, str]]
    CHARACTER_TO_HTML_ENTITY_RE: ClassVar[Pattern[Any]]
    CHARACTER_TO_XML_ENTITY: ClassVar[Dict[str, str]]
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
    sniffed_encoding: Optional[str]
    override_encodings: Iterable[str]
    exclude_encodings: Iterable[str]
    chardet_encoding: Optional[str]
    is_html: bool
    declared_encoding: Optional[str]
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
    def strip_byte_order_mark(cls, data: str) -> Tuple[str, None]: ...
    @overload
    @classmethod
    def strip_byte_order_mark(cls, data: bytes) -> Tuple[bytes, Optional[str]]: ...
    @overload
    @classmethod
    def strip_byte_order_mark(
        cls, data: Union[str, bytes]
    ) -> Tuple[Union[str, bytes], Optional[str]]: ...
    @classmethod
    def find_declared_encoding(
        cls,
        markup: Union[str, bytes],
        is_html: bool = ...,
        search_entire_document: bool = ...,
    ) -> Optional[str]: ...

class UnicodeDammit(Generic[AnyStr]):
    CHARSET_ALIASES: ClassVar[Dict[str, str]]
    ENCODINGS_WITH_SMART_QUOTES: ClassVar[List[str]]
    smart_quotes_to: Optional[Literal['ascii', 'html', 'xml']]
    tried_encodings: List[Tuple[str, Literal['strict', 'replace']]]
    contains_replacement_characters: bool
    is_html: bool
    log: Logger
    detector: EncodingDetector[AnyStr]
    markup: AnyStr
    unicode_markup: Optional[str]
    original_encoding: Optional[str]
    def __init__(
        self,
        markup: AnyStr,
        override_encodings: Iterable[str] = ...,
        smart_quotes_to: Optional[Literal['ascii', 'html', 'xml']] = ...,
        is_html: bool = ...,
        exclude_encodings: Iterable[str] = ...,
    ) -> None: ...
    @property
    def declared_html_encoding(self) -> Optional[str]: ...
    def find_codec(self, charset: str) -> Optional[CodecInfo]: ...
    MS_CHARS: ClassVar[Dict[bytes, Union[str, Tuple[str, str]]]]
    MS_CHARS_TO_ASCII: ClassVar[Dict[bytes, Union[str, Tuple[str, str]]]]
    WINDOWS_1252_TO_UTF8: ClassVar[Dict[int, bytes]]
    MULTIBYTE_MARKERS_AND_SIZES: ClassVar[List[Tuple[int, int, int]]]
    FIRST_MULTIBYTE_MARKER: ClassVar[int]
    LAST_MULTIBYTE_MARKER: ClassVar[int]
    @classmethod
    def detwingle(
        cls, in_bytes: AnyStr, main_encoding: str = ..., embedded_encoding: str = ...
    ) -> Union[str, bytes]: ...
