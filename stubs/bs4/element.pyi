from collections.abc import Callable, Container, Generator, Iterable, Iterator, Mapping
from re import Pattern
from typing import (
    Any,
    AnyStr,
    ClassVar,
    Final,
    Generic,
    Literal,
    NewType,
    NoReturn,
    Protocol,
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
PYTHON_SPECIFIC_ENCODINGS: Final[set[str]]

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
_TagStringFilterType = _FilterType['NavigableString | None', bool]
_TagAttrFilterType = _FilterType['str | None', bool]
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
    ) -> NavigableString | None: ...
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> NavigableString | None: ...
    @overload
    def __call__(
        self,
        name: _TagFilterType | None,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        text: _TagStringFilterType | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def __call__(
        self,
        *,
        attrs: _TagAttrFilterType | Mapping[str, _TagAttrFilterType | None] | None,
        text: _TagStringFilterType | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def __call__(
        self,
        *,
        text: _TagStringFilterType | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def __call__(
        self,
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        text: _TagStringFilterType | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | NavigableString | None: ...

@type_check_only
class _FindAllMethod(Protocol):
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        limit: int | None = ...,
        text: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: None = ...,
        *,
        limit: int | None = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def __call__(
        self,
        name: _TagFilterType | None,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        attrs: _TagAttrFilterType | Mapping[str, _TagAttrFilterType | None] | None,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        *,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def __call__(
        self,
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[NavigableString] | ResultSet[Tag]: ...

class NamespacedAttribute(str):
    prefix: str
    name: str | None
    namespace: str | None

class AttributeValueWithCharsetSubstitution(str): ...

class CharsetMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    original_value: str

class ContentMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    CHARSET_RE: ClassVar[Pattern[Any]]

class PageElement:
    parent: Tag | None
    previous_element: PageElement | None
    next_element: PageElement | None
    previous_sibling: PageElement | None
    next_sibling: PageElement | None
    previousSibling: PageElement | None
    nextSibling: PageElement | None
    def setup(
        self,
        parent: Tag | None = ...,
        previous_element: PageElement | None = ...,
        next_element: PageElement | None = ...,
        previous_sibling: PageElement | None = ...,
        next_sibling: PageElement | None = ...,
    ) -> None: ...
    def format_string(self, s: str, formatter: Formatter | None) -> str: ...
    @overload
    def formatter_for_name(self, formatter: _F) -> _F: ...
    @overload
    def formatter_for_name(
        self, formatter: _EntitySubstitutionCallback
    ) -> Formatter: ...
    @overload
    def formatter_for_name(self, formatter: str) -> Formatter: ...
    def replace_with(self: _PE, replace_with: str | PageElement) -> _PE | None: ...
    replaceWith = replace_with
    def unwrap(self: _PE) -> _PE: ...
    replace_with_children = unwrap
    replaceWithChildren = unwrap
    def wrap(self, wrap_inside: _PE) -> _PE: ...
    def extract(self: _PE, _self_index: int | None = ...) -> _PE: ...
    def insert(self, position: int, new_child: PageElement) -> None: ...
    def append(self, tag: PageElement) -> None: ...
    def extend(self, tags: PageElement | Iterable[PageElement]) -> None: ...
    def insert_before(self, *args: str | PageElement) -> None: ...
    def insert_after(self, *args: str | PageElement) -> None: ...
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
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        **kwargs: _TagAttrFilterType,
    ) -> Tag | None: ...
    findParent = find_parent
    def find_parents(
        self,
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        limit: int | None = ...,
        **kwargs: _TagAttrFilterType,
    ) -> ResultSet[Tag]: ...
    findParents = find_parents
    fetchParents = find_parents
    @property
    def next(self) -> PageElement | None: ...
    @property
    def previous(self) -> PageElement | None: ...
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
    known_xml: bool | None
    def __init__(self, value: AnyStr) -> None: ...
    @property
    def string(self) -> str: ...
    def output_ready(self, formatter: str | Formatter = ...) -> str: ...
    @property
    def name(self) -> None: ...

class PreformattedString(NavigableString):
    PREFIX: ClassVar[str]
    SUFFIX: ClassVar[str]
    def output_ready(self, formatter: str | Formatter | None = ...) -> str: ...

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
    parser_class: type[BeautifulSoup]
    name: str | None
    namespace: str | None
    prefix: str | None
    sourceline: int | None
    sourcepos: int | None
    known_xml: bool
    attrs: dict[str, str | list[str]]
    contents: list[PageElement]
    hidden: bool
    can_be_empty_element: bool | None
    cdata_list_attributes: bool | None
    preserve_whitespace_tags: bool | None
    builder: TreeBuilder | None
    parserClass: type[BeautifulSoup]
    string: str
    def __init__(
        self,
        parser: BeautifulSoup | None = ...,
        builder: TreeBuilder | None = ...,
        name: str | None = ...,
        namespace: str | None = ...,
        prefix: str | None = ...,
        attrs: Mapping[str, str | list[str]] | None = ...,
        parent: Tag | None = ...,
        previous: PageElement | None = ...,
        is_xml: bool | None = ...,
        sourceline: int | None = ...,
        sourcepos: int | None = ...,
        can_be_empty_element: bool | None = ...,
        cdata_list_attributes: bool | None = ...,
        preserve_whitespace_tags: bool | None = ...,
    ) -> None: ...
    @property
    def is_empty_element(self) -> bool: ...
    isSelfClosing = is_empty_element
    @property
    def strings(self) -> Iterator[NavigableString | CData]: ...
    @property
    def stripped_strings(self) -> Iterator[str]: ...
    def get_text(
        self,
        separator: str = ...,
        strip: bool = ...,
        types: Container[type[PageElement]] = ...,
    ) -> str: ...
    getText = get_text
    @property
    def text(self) -> str: ...
    def decompose(self) -> None: ...
    def clear(self, decompose: bool = ...) -> None: ...
    def smooth(self) -> None: ...
    def index(self, element: PageElement) -> int: ...
    @overload
    def get(self, key: str) -> str | list[str] | None: ...
    @overload
    def get(self, key: str, default: _T) -> str | list[str] | _T: ...
    @overload
    def get_attribute_list(self, key: str) -> list[str | None]: ...
    @overload
    def get_attribute_list(self, key: str, default: _T) -> list[str | _T]: ...
    def has_attr(self, key: str) -> bool: ...
    def __hash__(self) -> int: ...
    def __getitem__(self, key: str) -> str | list[str]: ...
    def __iter__(self) -> Iterator[PageElement]: ...
    def __len__(self) -> int: ...
    def __contains__(self, x: Any) -> bool: ...
    def __bool__(self) -> bool: ...
    def __setitem__(self, key: str, value: str | list[str]) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __getattr__(self, tag: str) -> Tag | None: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def encode(
        self,
        encoding: str = ...,
        indent_level: int | None = ...,
        formatter: str | Formatter = ...,
        errors: str = ...,
    ) -> bytes: ...
    def decode(
        self,
        indent_level: int | None = ...,
        eventual_encoding: str = ...,
        formatter: str | Formatter = ...,
    ) -> str: ...
    @overload
    def prettify(self, encoding: str, formatter: str | Formatter = ...) -> bytes: ...
    @overload
    def prettify(
        self, encoding: None = ..., formatter: str | Formatter = ...
    ) -> str: ...
    @overload
    def prettify(
        self, encoding: str | None, formatter: str | Formatter = ...
    ) -> str | bytes: ...
    def decode_contents(
        self,
        indent_level: int | None = ...,
        eventual_encoding: str = ...,
        formatter: str | Formatter = ...,
    ) -> str: ...
    def encode_contents(
        self,
        indent_level: int | None = ...,
        encoding: str = ...,
        formatter: str | Formatter = ...,
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
    ) -> NavigableString | None: ...
    @overload
    def find(
        self,
        name: None = ...,
        *,
        recursive: bool = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> NavigableString | None: ...
    @overload
    def find(
        self,
        name: _TagFilterType | None,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def find(
        self,
        *,
        attrs: _TagAttrFilterType | Mapping[str, _TagAttrFilterType | None] | None,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def find(
        self,
        *,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | None: ...
    @overload
    def find(
        self,
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> Tag | NavigableString | None: ...
    findChild = find
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        text: _StringFilterType,
        limit: int | None = ...,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        limit: int | None = ...,
        string: _StringFilterType,
        **kwargs: _Never,
    ) -> ResultSet[NavigableString]: ...
    @overload
    def find_all(
        self,
        name: _TagFilterType | None,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        *,
        attrs: _TagAttrFilterType | Mapping[str, _TagAttrFilterType | None] | None,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        *,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[Tag]: ...
    @overload
    def find_all(
        self,
        name: SoupStrainer | _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        recursive: bool = ...,
        text: _TagStringFilterType | None = ...,
        limit: int | None = ...,
        *,
        string: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> ResultSet[NavigableString] | ResultSet[Tag]: ...
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
        namespaces: Mapping[str, str] | None = ...,
        **kwargs: Any,
    ) -> Tag | None: ...
    def select(
        self,
        selector: str,
        namespaces: Mapping[str, str] | None = ...,
        limit: int | None = ...,
        **kwargs: Any,
    ) -> ResultSet[Tag]: ...
    def childGenerator(self) -> Iterator[PageElement]: ...
    def recursiveChildGenerator(self) -> Generator[PageElement, None, None]: ...
    def has_key(self, key: str) -> bool: ...

class SoupStrainer:
    name: _StrainerAttrType[Tag] | None
    attrs: dict[str, _StrainerAttrType[str | None] | None]
    text: _StrainerAttrType[NavigableString | None] | None
    def __init__(
        self,
        name: _TagFilterType | None = ...,
        attrs: _TagAttrFilterType
        | Mapping[str, _TagAttrFilterType | None]
        | None = ...,
        text: _TagStringFilterType | None = ...,
        **kwargs: _TagAttrFilterType | None,
    ) -> None: ...
    def search_tag(
        self,
        markup_name: str | Tag | None = ...,
        markup_attrs: dict[str, list[str] | tuple[str, ...]] = ...,
    ) -> PageElement | None: ...
    searchTag = search_tag
    def search(
        self,
        markup: str | Tag | Iterable[str | Tag],
    ) -> Tag | NavigableString | None: ...

class ResultSet(list[_T]):
    source: SoupStrainer
    def __init__(self, source: SoupStrainer, result: Iterable[_T] = ...) -> None: ...
    def __getattr__(self, key: Any) -> None: ...
