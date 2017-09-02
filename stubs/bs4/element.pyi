from typing import List, Union


class PageElement(object):
    pass


class NavigableString(str, PageElement):
    pass


class Tag(PageElement):
    @property
    def string(self) -> str: ...

    @string.setter
    def string(self, string) -> None: ...

    def select(self, selector: str) -> List['Tag']: ...

    def select_one(self, selector: str) -> 'Tag': ...

    def get_text(self, separator: str = ...,
                 strip: bool = ...) -> Union[str, NavigableString]: ...

    def decompose(self) -> None: ...
