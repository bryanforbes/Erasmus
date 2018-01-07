from typing import List, Union, Iterator, Optional, Dict


class PageElement(object):
    def replace_with(self, replace_with: Union[str, 'PageElement']) -> 'PageElement': ...

    def find_next_sibling(self, name: Optional[str] = ..., attrs: Dict[str, str] = ...,
                          text: Optional[str] = ..., **kwargs) -> 'Tag': ...

    def insert_before(self, tag: 'Tag') -> None: ...


class NavigableString(str, PageElement):
    pass


class Tag(PageElement):
    name: str
    string: str

    @property
    def contents(self) -> List['Tag']: ...

    @property
    def stripped_strings(self) -> Iterator[str]: ...

    @property
    def children(self) -> Iterator['Tag']: ...

    def select(self, selector: str) -> List['Tag']: ...

    def select_one(self, selector: str) -> 'Tag': ...

    def get_text(self, separator: str = ...,
                 strip: bool = ...) -> Union[str, NavigableString]: ...

    def decompose(self) -> None: ...

    def unwrap(self) -> 'Tag': ...
