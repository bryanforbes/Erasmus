from typing import Optional, List
import re

search_reference_re = re.compile(
    r'^(?P<book>.*) (?P<chapter_start>\d+):(?P<verse_start>\d+)'
    r'(?:-(?:(?P<chapter_end>\d+):)?(?P<verse_end>\d+))?$'
)


class Verse(object):
    __slots__ = ('chapter', 'verse')
    chapter: int
    verse: int

    def __init__(self, chapter: int, verse: int) -> None:
        self.chapter = chapter
        self.verse = verse

    def __str__(self) -> str:
        return f'{self.chapter}:{self.verse}'

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is Verse:
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Passage(object):
    __slots__ = ('book', 'start', 'end')

    book: str
    start: Verse
    end: Optional[Verse]

    def __init__(self, book: str, start: Verse, end: Verse = None) -> None:
        self.book = book
        self.start = start
        self.end = end

    @property
    def verses(self) -> str:
        verse = str(self.start)

        if self.end is not None:
            if self.end.chapter == self.start.chapter:
                verse += f'-{self.end.verse}'
            else:
                verse += f'-{self.end}'

        return verse

    def __str__(self) -> str:
        return f'{self.book} {self.verses}'

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is Passage:
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @classmethod
    def from_string(cls, verse: str) -> 'Passage':
        match = search_reference_re.match(verse)

        if match is None:
            return None

        chapter_start_int = int(match.group('chapter_start'))
        start = Verse(chapter_start_int, int(match.group('verse_start')))

        end = None  # type: Optional[Verse]
        end_str = match.group('verse_end')

        if end_str is not None:
            end_int = int(end_str)
            chapter_end_int = chapter_start_int

            chapter_end_str = match.group('chapter_end')
            if chapter_end_str is not None:
                chapter_end_int = int(chapter_end_str)

            end = Verse(chapter_end_int, end_int)

        return cls(
            match.group('book'),
            start,
            end
        )


class SearchResults(object):
    __slots__ = ('verses', 'total')

    verses: List[Passage]
    total: int

    def __init__(self, verses: List[Passage], total: int) -> None:
        self.verses = verses
        self.total = total

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        elif type(other) is SearchResults:
            return self.total == other.total and self.verses == other.verses
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
