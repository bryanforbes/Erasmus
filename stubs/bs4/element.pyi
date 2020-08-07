from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Pattern,
    TypeVar,
    Union,
)

class PageElement(object):
    def replace_with(self, replace_with: Union[str, PageElement]) -> PageElement: ...
    def find_next_sibling(
        self,
        name: Optional[str] = ...,
        attrs: Dict[str, str] = ...,
        text: Optional[str] = ...,
        **kwargs: Any,
    ) -> 'Tag': ...
    def insert_before(self, *args: Union[str, PageElement]) -> None: ...
    def insert_after(self, *args: Union[str, PageElement]) -> None: ...

class NavigableString(str, PageElement):
    name: None
    @property
    def string(self) -> str: ...

class Tag(PageElement):
    name: str
    string: str
    attrs: Dict[str, Any]
    @property
    def contents(self) -> List[Tag]: ...
    @property
    def stripped_strings(self) -> Iterator[str]: ...
    @property
    def children(self) -> Iterator[Tag]: ...
    @property
    def descendants(self) -> Generator[PageElement, None, None]: ...
    def select(self, selector: str) -> List[Tag]: ...
    def select_one(self, selector: str) -> Tag: ...
    def get_text(
        self, separator: str = ..., strip: bool = ...
    ) -> Union[str, NavigableString]: ...
    def decompose(self) -> None: ...
    def unwrap(self) -> Tag: ...

_StrainerArgType = Union[Pattern[str], Callable[[str], bool], bool]

class SoupStrainer(object):
    def __init__(
        self,
        name: Optional[Union[str, _StrainerArgType]] = ...,
        attrs: Dict[str, Any] = ...,
        text: Optional[Union[str, _StrainerArgType]] = ...,
        **kwargs: Any,
    ) -> None: ...
