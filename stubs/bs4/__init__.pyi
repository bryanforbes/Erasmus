from _typeshed import SupportsRead
from collections import Counter
from collections.abc import Mapping
from typing import Any, ClassVar

from .builder import (
    ParserRejectedMarkup as ParserRejectedMarkup,
    TreeBuilder,
    builder_registry as builder_registry,
)
from .dammit import UnicodeDammit as UnicodeDammit
from .element import (
    DEFAULT_OUTPUT_ENCODING as DEFAULT_OUTPUT_ENCODING,
    PYTHON_SPECIFIC_ENCODINGS as PYTHON_SPECIFIC_ENCODINGS,
    CData as CData,
    Comment as Comment,
    Declaration as Declaration,
    Doctype as Doctype,
    NavigableString as NavigableString,
    PageElement as PageElement,
    ProcessingInstruction as ProcessingInstruction,
    ResultSet as ResultSet,
    Script as Script,
    SoupStrainer as SoupStrainer,
    Stylesheet as Stylesheet,
    Tag as Tag,
    TemplateString as TemplateString,
)

class GuessedAtParserWarning(UserWarning): ...
class MarkupResemblesLocatorWarning(UserWarning): ...

class BeautifulSoup(Tag):
    ROOT_TAG_NAME: ClassVar[str]
    DEFAULT_BUILDER_FEATURES: ClassVar[list[str]]
    ASCII_SPACES: ClassVar[str]
    NO_PARSER_SPECIFIED_WARNING: ClassVar[str]
    element_classes: Mapping[type[Any], type[Any]]
    builder: TreeBuilder
    is_xml: bool
    known_xml: bool
    parse_only: SoupStrainer | None
    markup: None
    current_data: Any
    currentTag: Any
    tagStack: list[Any]
    open_tag_counter: Counter[str]
    preserve_whitespace_tag_stack: list[Any]
    string_container_stack: list[Any]
    def __init__(
        self,
        markup: str | bytes | SupportsRead[str] | SupportsRead[bytes] = ...,
        features: str | list[str] | None = ...,
        builder: TreeBuilder | type[TreeBuilder] | None = ...,
        parse_only: SoupStrainer | None = ...,
        from_encoding: str | None = ...,
        exclude_encodings: list[str] | None = ...,
        element_classes: Mapping[type[Any], type[Any]] | None = ...,
    ) -> None: ...
    def reset(self) -> None: ...
    def new_tag(
        self,
        name: str,
        namespace: str | None = ...,
        nsprefix: str | None = ...,
        attrs: Mapping[str, str] = ...,
        sourceline: int | None = ...,
        sourcepos: int | None = ...,
        **kwattrs: str,
    ) -> Tag: ...
    def string_container(self, base_class: type[Any] | None = ...) -> type[Any]: ...
    def new_string(self, s: str, subclass: type[Any] | None = ...) -> Any: ...
    def popTag(self) -> Any: ...
    def pushTag(self, tag: Any) -> None: ...
    def endData(self, containerClass: Any | None = ...) -> None: ...
    def object_was_parsed(
        self,
        o: Any,
        parent: Any | None = ...,
        most_recent_element: Any | None = ...,
    ) -> None: ...
    def handle_starttag(
        self,
        name: str,
        namespace: str | None,
        nsprefix: str | None,
        attrs: Mapping[str, str],
        sourceline: int | None = ...,
        sourcepos: int | None = ...,
    ) -> Tag | None: ...
    def handle_endtag(self, name: str, nsprefix: str | None = ...) -> None: ...
    def handle_data(self, data: Any) -> None: ...
    def decode(  # type: ignore
        self,
        pretty_print: bool = ...,
        eventual_encoding: str | None = ...,
        formatter: str = ...,
    ) -> str: ...

class BeautifulStoneSoup(BeautifulSoup):
    def __init__(
        self,
        markup: str | bytes | SupportsRead[str] | SupportsRead[bytes] = ...,
        features: str | list[str] | None = ...,
        builder: TreeBuilder | None = ...,
        parse_only: SoupStrainer | None = ...,
        from_encoding: str | None = ...,
        exclude_encodings: list[str] | None = ...,
        element_classes: Mapping[type[Any], type[Any]] | None = ...,
    ) -> None: ...

class StopParsing(Exception): ...
class FeatureNotFound(ValueError): ...
