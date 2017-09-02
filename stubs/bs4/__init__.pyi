from .element import (
    Tag,
    PageElement
)


class BeautifulSoup(Tag):
    def __init__(self, markup: str = ...,
                 features: str = None) -> None: ...
