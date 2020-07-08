# Service for querying Biola's Unbound Bible

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List

from attr import attrib, dataclass
from botus_receptus import re
from bs4 import BeautifulSoup
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import DoNotUnderstandError
from ..protocols import Bible
from .base_service import BaseService

number_re = re.compile(re.capture(re.one_or_more(re.DIGITS), re.DOT))

book_map: Dict[str, str] = {
    'Genesis': '01O',
    'Exodus': '02O',
    'Leviticus': '03O',
    'Numbers': '04O',
    'Deuteronomy': '05O',
    'Joshua': '06O',
    'Judges': '07O',
    'Ruth': '08O',
    '1 Samuel': '09O',
    '2 Samuel': '10O',
    '1 Kings': '11O',
    '2 Kings': '12O',
    '1 Chronicles': '13O',
    '2 Chronicles': '14O',
    'Ezra': '15O',
    'Nehemiah': '16O',
    'Esther': '17O',
    'Job': '18O',
    'Psalms': '19O',
    'Psalm': '19O',
    'Proverbs': '20O',
    'Ecclesiastes': '21O',
    'Song of Solomon': '22O',
    'Isaiah': '23O',
    'Jeremiah': '24O',
    'Lamentations': '25O',
    'Ezekiel': '26O',
    'Daniel': '27O',
    'Hosea': '28O',
    'Joel': '29O',
    'Amos': '30O',
    'Obadiah': '31O',
    'Jonah': '32O',
    'Micah': '33O',
    'Nahum': '34O',
    'Habakkuk': '35O',
    'Zephaniah': '36O',
    'Haggai': '37O',
    'Zechariah': '38O',
    'Malachi': '39O',
    'Matthew': '40N',
    'Mark': '41N',
    'Luke': '42N',
    'John': '43N',
    'Acts of the Apostles': '44N',
    'Romans': '45N',
    '1 Corinthians': '46N',
    '2 Corinthians': '47N',
    'Galatians': '48N',
    'Ephesians': '49N',
    'Philippians': '50N',
    'Colossians': '51N',
    '1 Thessalonians': '52N',
    '2 Thessalonians': '53N',
    '1 Timothy': '54N',
    '2 Timothy': '55N',
    'Titus': '56N',
    'Philemon': '57N',
    'Hebrews': '58N',
    'James': '59N',
    '1 Peter': '60N',
    '2 Peter': '61N',
    '1 John': '62N',
    '2 John': '63N',
    '3 John': '64N',
    'Jude': '65N',
    'Revelation': '66N',
    'Tobit': '67A',
    'Judith': '68A',
    'Greek Esther': '69A',
    'Wisdom': '70A',
    'Sirach': '71A',
    'Baruch': '72A',
    'Letter of Jeremiah': '73A',
    'Prayer of Azariah': '74A',
    'Susanna': '75A',
    'Bel and the Dragon': '76A',
    '1 Maccabees': '77A',
    '2 Maccabees': '78A',
    '3 Maccabees': '79A',
    '4 Maccabees': '80A',
    '1 Esdras': '81A',
    '2 Esdras': '82A',
    'Prayer of Manasseh': '83A',
    'Psalm 151': '84A',
    'Psalms of Solomon': '85A',
    'Odes': '86A',
}


@dataclass(slots=True)
class Unbound(BaseService):
    _base_url: URL = attrib(init=False)

    def __attrs_post_init__(self) -> None:
        self._base_url = URL(
            'http://unbound.biola.edu/index.cfm?method=searchResults.doSearch'
        )

    @asynccontextmanager
    async def _request_passage(
        self, bible: Bible, verses: VerseRange
    ) -> AsyncIterator[Passage]:
        url = self._base_url.update_query(
            {
                'search_type': 'simple_search',
                'parallel_1': bible.service_version,
                'book_section': '00',
                'book': book_map[verses.book],
                'displayFormat': 'normalNoHeader',
                'from_chap': str(verses.start.chapter),
                'from_verse': str(verses.start.verse),
            }
        )

        if verses.end:
            url = url.update_query(
                {'to_chap': str(verses.end.chapter), 'to_verse': str(verses.end.verse)}
            )

        async with self.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')

            verse_table = soup.select_one('table table table')

            if verse_table is None:
                raise DoNotUnderstandError

            rows = verse_table.select('tr')

            if rows[0].get_text('').strip() == 'No Verses Found':
                raise DoNotUnderstandError

            rtl = False
            for row in rows:
                cells = row.select('td')
                if len(cells) == 2 and cells[1].string == '\xa0':
                    rtl = True

                if (
                    len(cells) != 2
                    or cells[0].string == '\xa0'
                    or cells[1].string == '\xa0'
                ):
                    row.decompose()
                elif rtl:
                    cells[1].contents[0].insert_before(cells[1].contents[1])
                    cells[1].insert_before(cells[0])

            yield Passage(
                text=self._replace_special_escapes(
                    bible,
                    number_re.sub(r'__BOLD__\1__BOLD__', verse_table.get_text('')),
                ),
                range=verses,
                version=bible.abbr,
            )

    @asynccontextmanager
    async def _request_search(
        self, bible: Bible, terms: List[str], *, limit: int, offset: int
    ) -> AsyncIterator[SearchResults]:
        async with self.post(
            self._base_url,
            {
                'search_type': 'advanced_search',
                'parallel_1': bible.service_version,
                'displayFormat': 'normalNoHeader',
                'book_section': 'ALL',
                'book': 'ALL',
                'search': ' AND '.join(terms),
                'show_commentary': '0',
                'show_context': '0',
                'show_illustrations': '0',
                'show_maps': '0',
            },
        ) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')

            verse_table = soup.select_one('table table table')

            if verse_table is None:
                raise DoNotUnderstandError

            rows = verse_table.select('tr')

            if rows[0].get_text('').strip() == 'No Verses Found':
                yield SearchResults([], 0)
                return

            rows[0].decompose()
            rows[-2].decompose()
            rows[-1].decompose()

            passages: List[Passage] = []
            chapter_string = ''

            for row in verse_table.select('tr'):
                cells = row.select('td')
                if len(cells) < 2:
                    continue
                if cells[0].string == '\xa0':
                    chapter_string = row.get_text('').strip()
                else:
                    verse_string = cells[0].get_text('').strip()[:-1]
                    passage_text = cells[1].get_text('')
                    passages.append(
                        Passage(
                            text=self._replace_special_escapes(bible, passage_text),
                            range=VerseRange.from_string(
                                f'{chapter_string}:{verse_string}'
                            ),
                            version=bible.abbr,
                        )
                    )

            yield SearchResults(passages, len(passages))
