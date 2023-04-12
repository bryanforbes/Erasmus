from __future__ import annotations

from enum import Enum
from typing_extensions import override


class ConfessionType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'
    SECTIONS = 'SECTIONS'

    @override
    def __repr__(self, /) -> str:
        return f'<{self.__class__.__name__}.{self.name}>'


class NumberingType(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'
    ALPHA = 'ALPHA'

    @override
    def __repr__(self, /) -> str:
        return f'<{self.__class__.__name__}.{self.name}>'
