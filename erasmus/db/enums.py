from __future__ import annotations

from enum import Enum


class ConfessionType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'
    SECTIONS = 'SECTIONS'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class NumberingType(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'
    ALPHA = 'ALPHA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)
