from typing import Optional
from .element import Tag, PageElement  # noqa


class BeautifulSoup(Tag):
    def __init__(self, markup: str = ...,
                 features: Optional[str] = ...) -> None: ...
