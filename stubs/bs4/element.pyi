from typing import List, Union, Iterator


class PageElement(object):
    pass


class NavigableString(str, PageElement):
    pass


class Tag(PageElement):
    string: str

    @property
    def contents(self) -> List['Tag']: ...

    @property
    def stripped_strings(self) -> Iterator[str]: ...

    def select(self, selector: str) -> List['Tag']: ...

    def select_one(self, selector: str) -> 'Tag': ...

    def get_text(self, separator: str = ...,
                 strip: bool = ...) -> Union[str, NavigableString]: ...

    def decompose(self) -> None: ...

    def unwrap(self) -> 'Tag': ...
