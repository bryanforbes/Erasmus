from typing import Optional
from .element import Tag as Tag, PageElement as PageElement  # noqa

class BeautifulSoup(Tag):
    def __init__(self, markup: str = ..., features: Optional[str] = ...) -> None: ...
