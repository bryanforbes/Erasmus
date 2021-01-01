from collections import Counter
from typing import (
    Any,
    ClassVar,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    type_check_only,
)
from typing_extensions import Protocol

from .builder import ParserRejectedMarkup as ParserRejectedMarkup
from .builder import TreeBuilder
from .builder import builder_registry as builder_registry
from .dammit import UnicodeDammit as UnicodeDammit
from .element import DEFAULT_OUTPUT_ENCODING as DEFAULT_OUTPUT_ENCODING
from .element import PYTHON_SPECIFIC_ENCODINGS as PYTHON_SPECIFIC_ENCODINGS
from .element import CData as CData
from .element import Comment as Comment
from .element import Declaration as Declaration
from .element import Doctype as Doctype
from .element import NavigableString as NavigableString
from .element import PageElement as PageElement
from .element import ProcessingInstruction as ProcessingInstruction
from .element import ResultSet as ResultSet
from .element import Script as Script
from .element import SoupStrainer as SoupStrainer
from .element import Stylesheet as Stylesheet
from .element import Tag as Tag
from .element import TemplateString as TemplateString

_T = TypeVar('_T')
_T_co = TypeVar('_T_co', covariant=True)
@type_check_only
class _FileLike(Protocol[_T_co]):
    def read(self) -> _T_co: ...

class GuessedAtParserWarning(UserWarning): ...
class MarkupResemblesLocatorWarning(UserWarning): ...

_BS = TypeVar('_BS', bound=BeautifulSoup)

class BeautifulSoup(Tag):
    ROOT_TAG_NAME: ClassVar[str]
    DEFAULT_BUILDER_FEATURES: ClassVar[List[str]]
    ASCII_SPACES: ClassVar[str]
    NO_PARSER_SPECIFIED_WARNING: ClassVar[str]
    element_classes: Mapping[Type[Any], Type[Any]]
    builder: TreeBuilder
    is_xml: bool
    known_xml: bool
    parse_only: Optional[SoupStrainer]
    markup: None
    current_data: Any
    currentTag: Any
    tagStack: List[Any]
    open_tag_counter: Counter[str]
    preserve_whitespace_tag_stack: List[Any]
    string_container_stack: List[Any]
    def __init__(
        self,
        markup: Union[str, bytes, _FileLike[str], _FileLike[bytes]] = ...,
        features: Optional[Union[str, List[str]]] = ...,
        builder: Optional[Union[TreeBuilder, Type[TreeBuilder]]] = ...,
        parse_only: Optional[SoupStrainer] = ...,
        from_encoding: Optional[str] = ...,
        exclude_encodings: Optional[List[str]] = ...,
        element_classes: Optional[Mapping[Type[Any], Type[Any]]] = ...,
    ): ...
    def reset(self) -> None: ...
    def new_tag(
        self,
        name: str,
        namespace: Optional[str] = ...,
        nsprefix: Optional[str] = ...,
        attrs: Mapping[str, str] = ...,
        sourceline: Optional[int] = ...,
        sourcepos: Optional[int] = ...,
        **kwattrs: str,
    ) -> Tag: ...
    def string_container(self, base_class: Optional[Type[Any]] = ...) -> Type[Any]: ...
    def new_string(self, s: str, subclass: Optional[Type[Any]] = ...) -> Any: ...
    def popTag(self) -> Any: ...
    def pushTag(self, tag: Any) -> None: ...
    def endData(self, containerClass: Optional[Any] = ...) -> None: ...
    def object_was_parsed(
        self,
        o: Any,
        parent: Optional[Any] = ...,
        most_recent_element: Optional[Any] = ...,
    ) -> None: ...
    def handle_starttag(
        self,
        name: str,
        namespace: Optional[str],
        nsprefix: Optional[str],
        attrs: Mapping[str, str],
        sourceline: Optional[int] = ...,
        sourcepos: Optional[int] = ...,
    ) -> Optional[Tag]: ...
    def handle_endtag(self, name: str, nsprefix: Optional[str] = ...) -> None: ...
    def handle_data(self, data: Any) -> None: ...
    def decode(  # type: ignore[override]
        self,
        pretty_print: bool = ...,
        eventual_encoding: Optional[str] = ...,
        formatter: str = ...,
    ) -> str: ...

class BeautifulStoneSoup(BeautifulSoup):
    def __init__(
        self,
        markup: Union[str, bytes, _FileLike[str], _FileLike[bytes]] = ...,
        features: Optional[Union[str, List[str]]] = ...,
        builder: Optional[TreeBuilder] = ...,
        parse_only: Optional[SoupStrainer] = ...,
        from_encoding: Optional[str] = ...,
        exclude_encodings: Optional[List[str]] = ...,
        element_classes: Optional[Mapping[Type[Any], Type[Any]]] = ...,
    ): ...

class StopParsing(Exception): ...
class FeatureNotFound(ValueError): ...
