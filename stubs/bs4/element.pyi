from collections.abc import Callable, Container, Generator, Iterable, Iterator, Mapping
from re import Pattern
from typing import (
    Any,
    AnyStr,
    ClassVar,
    Dict,
    Final,
    Generic,
    List,
    Literal,
    NewType,
    NoReturn,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
    type_check_only,
)

from . import BeautifulSoup
from .builder import TreeBuilder
from .formatter import Formatter, _EntitySubstitutionCallback

DEFAULT_OUTPUT_ENCODING: Final[str]
PY3K: Final[bool]
nonwhitespace_re: Final[Pattern[Any]]
whitespace_re: Final[Pattern[Any]]
PYTHON_SPECIFIC_ENCODINGS: Final[Set[str]]

_F = TypeVar('_F', bound=Formatter)
_PE = TypeVar('_PE', bound=PageElement)
_T = TypeVar('_T')
_U = TypeVar('_U')
_T_contra = TypeVar('_T_contra', contravariant=True)
_Never = NewType('_Never', object)
@type_check_only
class _StrainerCallable(Protocol[_T_contra]):
    def __call__(self, __markup: _T_contra) -> bool: ...

_FilterBaseType = Union[str, _StrainerCallable[_T], Pattern[Any], _U]
_FilterIterableType = Iterable[Union[None, _T, Iterable[Any]]]
_StrainerAttrType = Union[
    _FilterBaseType[_T, bool], _FilterIterableType[_FilterBaseType[_T, bool]]
]
_FilterItemType = Union[bytes, _FilterBaseType[_T, _U]]
_FilterType = Union[
    _FilterItemType[_T, _U], _FilterIterableType[_FilterItemType[_T, _U]]
]
_StringFilterType = _FilterType[NavigableString, Literal[True]]
_TagStringFilterType = _FilterType[Optional[NavigableString], bool]
_TagAttrFilterType = _FilterType[Optional[str], bool]
_TagFilterType = _FilterType[Tag, bool]
@type_check_only
class _FindOneMethod(Protocol):
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        text: _StringFilterType,
        **kwargs: _Never,
    ) -> Optional[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> Optional[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: Optional[_TagFilterType],
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        text: Optional[_TagStringFilterType] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ],
        text: Optional[_TagStringFilterType] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        text: Optional[_TagStringFilterType] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def __call__(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        text: Optional[_TagStringFilterType] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Union[Tag, NavigableString]]: ...

@type_check_only
class _FindAllMethod(Protocol):
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        limit: Optional[int] = ...,
        text: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        limit: Optional[int] = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: Optional[_TagFilterType],
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ],
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Union[ResultSet[NavigableString], ResultSet[Tag]]: ...

class NamespacedAttribute(str):
    prefix: str
    name: Optional[str]
    namespace: Optional[str]

class AttributeValueWithCharsetSubstitution(str): ...

class CharsetMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    original_value: str

class ContentMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    CHARSET_RE: ClassVar[Pattern[Any]]

class PageElement:
    parent: Optional[Tag]
    previous_element: Optional[PageElement]
    next_element: Optional[PageElement]
    previous_sibling: Optional[PageElement]
    next_sibling: Optional[PageElement]
    previousSibling: Optional[PageElement]
    nextSibling: Optional[PageElement]
    def setup(
        self,
        parent: Optional[Tag] = ...,
        previous_element: Optional[PageElement] = ...,
        next_element: Optional[PageElement] = ...,
        previous_sibling: Optional[PageElement] = ...,
        next_sibling: Optional[PageElement] = ...,
    ) -> None: ...
    def format_string(self, s: str, formatter: Optional[Formatter]) -> str: ...
    @overload
    def formatter_for_name(self, formatter: _F) -> _F: ...
    @overload
    def formatter_for_name(
        self, formatter: _EntitySubstitutionCallback
    ) -> Formatter: ...
    @overload
    def formatter_for_name(self, formatter: str) -> Formatter: ...
    def replace_with(
        self: _PE, replace_with: Union[str, PageElement]
    ) -> Optional[_PE]: ...
    replaceWith = replace_with
    def unwrap(self: _PE) -> _PE: ...
    replace_with_children = unwrap
    replaceWithChildren = unwrap
    def wrap(self, wrap_inside: _PE) -> _PE: ...
    def extract(self: _PE, _self_index: Optional[int] = ...) -> _PE: ...
    def insert(self, position: int, new_child: PageElement) -> None: ...
    def append(self, tag: PageElement) -> None: ...
    def extend(self, tags: Union[PageElement, Iterable[PageElement]]) -> None: ...
    def insert_before(self, *args: Union[str, PageElement]) -> None: ...
    def insert_after(self, *args: Union[str, PageElement]) -> None: ...
    find_next: ClassVar[_FindOneMethod]
    findNext: ClassVar[_FindOneMethod]
    find_all_next: ClassVar[_FindAllMethod]
    findAllNext: ClassVar[_FindAllMethod]
    find_next_sibling: ClassVar[_FindOneMethod]
    findNextSibling: ClassVar[_FindOneMethod]
    find_next_siblings: ClassVar[_FindAllMethod]
    findNextSiblings: ClassVar[_FindAllMethod]
    fetchNextSiblings: ClassVar[_FindAllMethod]
    find_previous: ClassVar[_FindOneMethod]
    findPrevious: ClassVar[_FindOneMethod]
    find_all_previous: ClassVar[_FindAllMethod]
    findAllPrevious: ClassVar[_FindAllMethod]
    fetchPrevious: ClassVar[_FindAllMethod]
    find_previous_sibling: ClassVar[_FindOneMethod]
    findPreviousSibling: ClassVar[_FindOneMethod]
    find_previous_siblings: ClassVar[_FindAllMethod]
    findPreviousSiblings: ClassVar[_FindAllMethod]
    fetchPreviousSiblings: ClassVar[_FindAllMethod]
    def find_parent(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        **kwargs: _TagAttrFilterType,
    ) -> Optional[Tag]: ...
    findParent = find_parent
    def find_parents(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        limit: Optional[int] = ...,
        **kwargs: _TagAttrFilterType,
    ) -> ResultSet[Tag]: ...
    findParents = find_parents
    fetchParents = find_parents
    @property
    def next(self) -> Optional[PageElement]: ...
    @property
    def previous(self) -> Optional[PageElement]: ...
    @property
    def next_elements(self) -> Iterable[PageElement]: ...
    @property
    def next_siblings(self) -> Iterable[PageElement]: ...
    @property
    def previous_elements(self) -> Iterable[PageElement]: ...
    @property
    def previous_siblings(self) -> Iterable[PageElement]: ...
    @property
    def parents(self) -> Iterable[PageElement]: ...
    @property
    def decomposed(self) -> bool: ...
    def nextGenerator(self) -> Iterable[PageElement]: ...
    def nextSiblingGenerator(self) -> Iterable[PageElement]: ...
    def previousGenerator(self) -> Iterable[PageElement]: ...
    def previousSiblingGenerator(self) -> Iterable[PageElement]: ...
    def parentGenerator(self) -> Iterable[PageElement]: ...

class NavigableString(str, PageElement):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]
    known_xml: Optional[bool]
    def __init__(self, value: AnyStr) -> None: ...
    @property
    def string(self) -> str: ...
    def output_ready(self, formatter: Union[str, Formatter] = ...) -> str: ...
    @property
    def name(self) -> None: ...

class PreformattedString(NavigableString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]
    def output_ready(self, formatter: Optional[Union[str, Formatter]] = ...) -> str: ...

class CData(PreformattedString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class ProcessingInstruction(PreformattedString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class XMLProcessingInstruction(ProcessingInstruction):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class Comment(PreformattedString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class Declaration(PreformattedString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class Doctype(PreformattedString):
    @classmethod
    def for_name_and_ids(cls, name: str, pub_id: str, system_id: str) -> Doctype: ...
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]

class Stylesheet(NavigableString): ...
class Script(NavigableString): ...
class TemplateString(NavigableString): ...

class Tag(PageElement):
    parser_class: Type[BeautifulSoup]
    name: Optional[str]
    namespace: Optional[str]
    prefix: Optional[str]
    sourceline: Optional[int]
    sourcepos: Optional[int]
    known_xml: bool
    attrs: Dict[str, Union[str, List[str]]]
    contents: List[PageElement]
    hidden: bool
    can_be_empty_element: Optional[bool]
    cdata_list_attributes: Optional[bool]
    preserve_whitespace_tags: Optional[bool]
    builder: Optional[TreeBuilder]
    parserClass: Type[BeautifulSoup]
    string: str
    def __init__(
        self,
        parser: Optional[BeautifulSoup] = ...,
        builder: Optional[TreeBuilder] = ...,
        name: Optional[str] = ...,
        namespace: Optional[str] = ...,
        prefix: Optional[str] = ...,
        attrs: Optional[Mapping[str, Union[str, List[str]]]] = ...,
        parent: Optional[Tag] = ...,
        previous: Optional[PageElement] = ...,
        is_xml: Optional[bool] = ...,
        sourceline: Optional[int] = ...,
        sourcepos: Optional[int] = ...,
        can_be_empty_element: Optional[bool] = ...,
        cdata_list_attributes: Optional[bool] = ...,
        preserve_whitespace_tags: Optional[bool] = ...,
    ) -> None: ...
    @property
    def is_empty_element(self) -> bool: ...
    isSelfClosing = is_empty_element
    @property
    def strings(self) -> Iterator[Union[NavigableString, CData]]: ...
    @property
    def stripped_strings(self) -> Iterator[str]: ...
    def get_text(
        self,
        separator: str = ...,
        strip: bool = ...,
        types: Container[Type[PageElement]] = ...,
    ) -> str: ...
    getText = get_text
    @property
    def text(self) -> str: ...
    def decompose(self) -> None: ...
    def clear(self, decompose: bool = ...) -> None: ...
    def smooth(self) -> None: ...
    def index(self, element: PageElement) -> int: ...
    @overload
    def get(self, key: str) -> Optional[Union[str, List[str]]]: ...
    @overload
    def get(self, key: str, default: _T) -> Union[str, List[str], _T]: ...
    @overload
    def get_attribute_list(self, key: str) -> List[Optional[str]]: ...
    @overload
    def get_attribute_list(self, key: str, default: _T) -> List[Union[str, _T]]: ...
    def has_attr(self, key: str) -> bool: ...
    def __hash__(self) -> int: ...
    def __getitem__(self, key: str) -> Union[str, List[str]]: ...
    def __iter__(self) -> Iterator[PageElement]: ...
    def __len__(self) -> int: ...
    def __contains__(self, x: Any) -> bool: ...
    def __bool__(self) -> bool: ...
    def __setitem__(self, key: str, value: Union[str, List[str]]) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __getattr__(self, tag: str) -> Optional[Tag]: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def encode(
        self,
        encoding: str = ...,
        indent_level: Optional[int] = ...,
        formatter: Union[str, Formatter] = ...,
        errors: str = ...,
    ) -> bytes: ...
    def decode(
        self,
        indent_level: Optional[int] = ...,
        eventual_encoding: str = ...,
        formatter: Union[str, Formatter] = ...,
    ) -> str: ...
    @overload
    def prettify(
        self, encoding: str, formatter: Union[str, Formatter] = ...
    ) -> bytes: ...
    @overload
    def prettify(
        self, encoding: None = ..., formatter: Union[str, Formatter] = ...
    ) -> str: ...
    @overload
    def prettify(
        self, encoding: Optional[str], formatter: Union[str, Formatter] = ...
    ) -> Union[str, bytes]: ...
    def decode_contents(
        self,
        indent_level: Optional[int] = ...,
        eventual_encoding: str = ...,
        formatter: Union[str, Formatter] = ...,
    ) -> str: ...
    def encode_contents(
        self,
        indent_level: Optional[int] = ...,
        encoding: str = ...,
        formatter: Union[str, Formatter] = ...,
    ) -> bytes: ...
    def renderContents(
        self, encoding: str = ..., prettyPrint: bool = ..., indentLevel: int = ...
    ) -> bytes: ...
    @overload
    def find(
        self,
        name: None = ...,
        *,
        recursive: bool = ...,
        text: _StringFilterType,
        **kwargs: _Never,
    ) -> Optional[NavigableString]: ...
    @overload
    def find(
        self,
        name: None = ...,
        *,
        recursive: bool = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> Optional[NavigableString]: ...
    @overload
    def find(
        self,
        name: Optional[_TagFilterType],
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def find(
        self,
        *,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ],
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def find(
        self,
        *,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Tag]: ...
    @overload
    def find(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Optional[Union[Tag, NavigableString]]: ...
    findChild = find
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        text: _StringFilterType,
        limit: Optional[int] = ...,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        limit: Optional[int] = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def find_all(
        self,
        name: Optional[_TagFilterType],
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        *,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ],
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        name: Optional[Union[SoupStrainer, _TagFilterType]] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        recursive: bool = ...,
        text: Optional[_TagStringFilterType] = ...,
        limit: Optional[int] = ...,
        *,
        string: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> Union[ResultSet[NavigableString], ResultSet[Tag]]: ...
    findAll = find_all
    findChildren = find_all
    __call__ = find_all
    @property
    def children(self) -> Iterator[PageElement]: ...
    @property
    def descendants(self) -> Generator[PageElement, None, None]: ...
    def select_one(
        self,
        selector: str,
        namespaces: Optional[Mapping[str, str]] = ...,
        **kwargs: Any,
    ) -> Optional[Tag]: ...
    def select(
        self,
        selector: str,
        namespaces: Optional[Mapping[str, str]] = ...,
        limit: Optional[int] = ...,
        **kwargs: Any,
    ) -> ResultSet[Tag]: ...
    def childGenerator(self) -> Iterator[PageElement]: ...
    def recursiveChildGenerator(self) -> Generator[PageElement, None, None]: ...
    def has_key(self, key: str) -> bool: ...

class SoupStrainer:
    name: Optional[_StrainerAttrType[Tag]]
    attrs: Dict[str, Optional[_StrainerAttrType[Optional[str]]]]
    text: Optional[_StrainerAttrType[Optional[NavigableString]]]
    def __init__(
        self,
        name: Optional[_TagFilterType] = ...,
        attrs: Optional[
            Union[_TagAttrFilterType, Mapping[str, Optional[_TagAttrFilterType]]]
        ] = ...,
        text: Optional[_TagStringFilterType] = ...,
        **kwargs: Optional[_TagAttrFilterType],
    ) -> None: ...
    def search_tag(
        self,
        markup_name: Optional[Union[str, Tag]] = ...,
        markup_attrs: Dict[str, Union[List[str], Tuple[str, ...]]] = ...,
    ) -> Optional[PageElement]: ...
    searchTag = search_tag
    def search(
        self,
        markup: Union[str, Tag, Iterable[Union[str, Tag]]],
    ) -> Optional[Union[Tag, NavigableString]]: ...

class ResultSet(List[_T]):
    source: SoupStrainer
    def __init__(self, source: SoupStrainer, result: Iterable[_T] = ...) -> None: ...
    def __getattr__(self, key: Any) -> None: ...
