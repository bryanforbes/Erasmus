from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Dict, Final, List, Optional

import aiohttp
from attr import dataclass
from botus_receptus import re

from ..data import Passage, SearchResults, VerseRange
from ..protocols import Bible

_log: Final = logging.getLogger(__name__)

_whitespace_re: Final = re.compile(re.one_or_more(re.WHITESPACE))
_bold_re: Final = re.compile(r'__BOLD__')
_italic_re: Final = re.compile(r'__ITALIC__')
_specials_re: Final = re.compile(re.capture(r'[\*`]'))
_number_re: Final = re.compile(
    re.capture(r'\*\*', re.one_or_more(re.DIGIT), re.DOT, r'\*\*')
)


@dataclass(slots=True)
class BaseService(object):
    session: aiohttp.ClientSession
    config: Optional[Dict[str, Any]]

    @abstractmethod
    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        ...

    @abstractmethod
    async def search(
        self, bible: Bible, terms: List[str], *, limit: int = 20, offset: int = 0
    ) -> SearchResults:
        ...

    def replace_special_escapes(self, bible: Bible, text: str) -> str:
        text = _whitespace_re.sub(' ', text.strip())
        text = _specials_re.sub(r'\\\1', text)
        text = _bold_re.sub('**', text)
        text = _italic_re.sub('_', text)

        if bible.rtl:
            # wrap in [RTL embedding]text[Pop directional formatting]
            text = _number_re.sub('\u202b\\1\u202c', text)

        return text
