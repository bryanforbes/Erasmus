from collections.abc import Container, Iterator
from typing import Any, ClassVar, Final, NewType, override

from .. import BeautifulSoup
from ..element import Tag

class TreeBuilderRegistry:
    builders_for_feature: dict[str, list[type[TreeBuilder]]]
    builders: list[type[TreeBuilder]]
    def __init__(self) -> None: ...
    def register(self, treebuilder_class: type[TreeBuilder]) -> None: ...
    def lookup(self, *features: str) -> type[TreeBuilder] | None: ...

builder_registry: Final[TreeBuilderRegistry]

_UseDefault = NewType('_UseDefault', object)

class TreeBuilder:
    NAME: ClassVar[str]
    ALTERNATE_NAMES: ClassVar[list[str]]
    features: ClassVar[list[str]]
    is_xml: ClassVar[bool]
    picklable: ClassVar[bool]
    empty_element_tags: ClassVar[Container[str] | None]
    DEFAULT_CDATA_LIST_ATTRIBUTES: ClassVar[dict[str, Container[str]]]
    DEFAULT_PRESERVE_WHITESPACE_TAGS: ClassVar[Container[str]]
    DEFAULT_STRING_CONTAINERS: ClassVar[dict[str, type[Any]]]
    USE_DEFAULT: ClassVar[_UseDefault]
    TRACKS_LINE_NUMBERS: ClassVar[bool]
    soup: BeautifulSoup | None
    cdata_list_attributes: dict[str, Container[str]] | None
    preserve_whitespace_tags: Container[str] | None
    store_line_numbers: bool
    string_containers: dict[str, type[Any]]
    def __init__(
        self,
        multi_valued_attributes: _UseDefault | None | dict[str, Container[str]] = ...,
        preserve_whitespace_tags: _UseDefault | None | Container[str] = ...,
        store_line_numbers: _UseDefault | bool = ...,
        string_containers: _UseDefault | dict[str, type[Any]] = ...,
    ) -> None: ...
    def initialize_soup(self, soup: BeautifulSoup) -> None: ...
    def reset(self) -> None: ...
    def can_be_empty_element(self, tag_name: str) -> bool: ...
    def feed(self, markup: str) -> None: ...
    def prepare_markup(
        self,
        markup: str,
        user_specified_encoding: str | None = ...,
        document_declared_encoding: str | None = ...,
        exclude_encodings: list[str] | None = ...,
    ) -> Iterator[tuple[str, str | None, str | None, bool]]: ...
    def test_fragment_to_document(self, fragment: str) -> str: ...
    def set_up_substitutions(self, tag: Tag) -> bool: ...

class SAXTreeBuilder(TreeBuilder):
    def close(self) -> None: ...
    def startElement(self, name: str, attrs: Any) -> None: ...
    def endElement(self, name: str) -> None: ...
    def startElementNS(self, nsTuple: Any, nodeName: Any, attrs: Any) -> None: ...
    def endElementNS(self, nsTuple: Any, nodeName: Any) -> None: ...
    def startPrefixMapping(self, prefix: Any, nodeValue: Any) -> None: ...
    def endPrefixMapping(self, prefix: Any) -> None: ...
    def characters(self, content: Any) -> None: ...
    def startDocument(self) -> None: ...
    def endDocument(self) -> None: ...

class HTMLTreeBuilder(TreeBuilder):
    empty_element_tags: ClassVar[Container[str] | None]
    block_elements: ClassVar[set[str] | None]
    DEFAULT_STRING_CONTAINERS: ClassVar[dict[str, type[Any]]]
    DEFAULT_CDATA_LIST_ATTRIBUTES: ClassVar[dict[str, Container[str]]]
    DEFAULT_PRESERVE_WHITESPACE_TAGS: ClassVar[Container[str]]
    @override
    def set_up_substitutions(self, tag: Tag) -> bool: ...

class ParserRejectedMarkup(Exception): ...
