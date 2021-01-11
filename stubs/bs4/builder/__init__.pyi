from collections.abc import Container, Iterator
from typing import (
    Any,
    ClassVar,
    Dict,
    Final,
    List,
    NewType,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

from .. import BeautifulSoup
from ..element import Tag

class TreeBuilderRegistry:
    builders_for_feature: Dict[str, List[Type[TreeBuilder]]]
    builders: List[Type[TreeBuilder]]
    def __init__(self) -> None: ...
    def register(self, treebuilder_class: Type[TreeBuilder]) -> None: ...
    def lookup(self, *features: str) -> Optional[Type[TreeBuilder]]: ...

builder_registry: Final[TreeBuilderRegistry]

_UseDefault = NewType('_UseDefault', object)

class TreeBuilder:
    NAME: ClassVar[str]
    ALTERNATE_NAMES: ClassVar[List[str]]
    features: ClassVar[List[str]]
    is_xml: ClassVar[bool]
    picklable: ClassVar[bool]
    empty_element_tags: ClassVar[Optional[Container[str]]]
    DEFAULT_CDATA_LIST_ATTRIBUTES: ClassVar[Dict[str, Container[str]]]
    DEFAULT_PRESERVE_WHITESPACE_TAGS: ClassVar[Container[str]]
    DEFAULT_STRING_CONTAINERS: ClassVar[Dict[str, Type[Any]]]
    USE_DEFAULT: ClassVar[_UseDefault]
    TRACKS_LINE_NUMBERS: ClassVar[bool]
    soup: Optional[BeautifulSoup]
    cdata_list_attributes: Optional[Dict[str, Container[str]]]
    preserve_whitespace_tags: Optional[Container[str]]
    store_line_numbers: bool
    string_containers: Dict[str, Type[Any]]
    def __init__(
        self,
        multi_valued_attributes: Union[
            _UseDefault, None, Dict[str, Container[str]]
        ] = ...,
        preserve_whitespace_tags: Union[_UseDefault, None, Container[str]] = ...,
        store_line_numbers: Union[_UseDefault, bool] = ...,
        string_containers: Union[_UseDefault, Dict[str, Type[Any]]] = ...,
    ) -> None: ...
    def initialize_soup(self, soup: BeautifulSoup) -> None: ...
    def reset(self) -> None: ...
    def can_be_empty_element(self, tag_name: str) -> bool: ...
    def feed(self, markup: str) -> None: ...
    def prepare_markup(
        self,
        markup: str,
        user_specified_encoding: Optional[str] = ...,
        document_declared_encoding: Optional[str] = ...,
        exclude_encodings: Optional[List[str]] = ...,
    ) -> Iterator[Tuple[str, Optional[str], Optional[str], bool]]: ...
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
    empty_element_tags: ClassVar[Optional[Container[str]]]
    block_elements: ClassVar[Optional[Set[str]]]
    DEFAULT_STRING_CONTAINERS: ClassVar[Dict[str, Type[Any]]]
    DEFAULT_CDATA_LIST_ATTRIBUTES: ClassVar[Dict[str, Container[str]]]
    DEFAULT_PRESERVE_WHITESPACE_TAGS: ClassVar[Container[str]]
    def set_up_substitutions(self, tag: Tag) -> bool: ...

class ParserRejectedMarkup(Exception): ...
