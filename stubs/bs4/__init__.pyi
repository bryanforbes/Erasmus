from typing import Optional

from .element import NavigableString as NavigableString
from .element import PageElement as PageElement
from .element import SoupStrainer as SoupStrainer
from .element import Tag as Tag

class BeautifulSoup(Tag):
    def __init__(
        self,
        markup: str = ...,
        features: Optional[str] = ...,
        parse_only: Optional[SoupStrainer] = ...,
    ) -> None: ...
