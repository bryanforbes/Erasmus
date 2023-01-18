from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Final

from botus_receptus import re

from ..utils import frozen

if TYPE_CHECKING:
    from typing_extensions import Self

    import aiohttp

    from ..config import ServiceConfig
    from ..data import Passage, SearchResults, VerseRange
    from ..types import Bible

_log: Final = logging.getLogger(__name__)

_whitespace_re: Final = re.compile(re.one_or_more(re.WHITESPACE))
_punctuation_re: Final = re.compile(
    re.one_or_more(re.WHITESPACE), re.capture(r'[,.;:]'), re.one_or_more(re.WHITESPACE)
)
_bold_re: Final = re.compile(r'__BOLD__')
_italic_re: Final = re.compile(r'__ITALIC__')
_specials_re: Final = re.compile(re.capture(r'[\*`]'))
_number_re: Final = re.compile(
    re.capture(r'\*\*', re.one_or_more(re.DIGIT), re.DOT, r'\*\*')
)


@frozen
class BaseService:
    session: aiohttp.ClientSession
    config: ServiceConfig | None

    @abstractmethod
    async def get_passage(self, bible: Bible, verses: VerseRange, /) -> Passage:
        ...

    @abstractmethod
    async def search(
        self, bible: Bible, terms: list[str], /, *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        ...

    def replace_special_escapes(self, bible: Bible, text: str, /) -> str:
        text = _whitespace_re.sub(' ', text.strip())
        text = _punctuation_re.sub(r'\1 ', text)
        text = _specials_re.sub(r'\\\1', text)
        text = _bold_re.sub('**', text)
        text = _italic_re.sub('_', text)

        if bible.rtl:
            # wrap in [RTL embedding]text[Pop directional formatting]
            text = _number_re.sub('\u202b\\1\u202c', text)

        return text

    @classmethod
    def from_config(
        cls, config: ServiceConfig | None, session: aiohttp.ClientSession, /
    ) -> Self:
        return cls(session, config)
