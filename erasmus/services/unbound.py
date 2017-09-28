# Service for querying Biola's Unbound Bible

from typing import Dict, List  # noqa
from bs4 import BeautifulSoup, Tag
from aiohttp import ClientResponse
from urllib.parse import urlencode

from ..service import Service
from ..data import VerseRange, SearchResults
from ..exceptions import DoNotUnderstandError

import re

number_re = re.compile(r'(\d+\.)')

book_map = {
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
    'Odes': '86A'
}  # type: Dict[str, str]


class Unbound(Service[Tag]):
    base_url = 'http://unbound.biola.edu/index.cfm?method=searchResults.doSearch'

    async def _process_response(self, response: ClientResponse) -> Tag:
        text = await response.text()
        return BeautifulSoup(text, 'html.parser')

    def _get_passage_url(self, version: str, verses: VerseRange) -> str:
        query = {
            'search_type': 'simple_search',
            'parallel_1': version,
            'book_section': '00',
            'book': book_map[verses.book],
            'displayFormat': 'normalNoHeader',
            'from_chap': str(verses.start.chapter),
            'from_verse': str(verses.start.verse)
        }  # type: Dict[str, str]

        if (verses.end):
            query.update({
                'to_chap': str(verses.end.chapter),
                'to_verse': str(verses.end.verse)
            })

        return f'{self.base_url}&' + urlencode(query)

    def _get_passage_text(self, response: Tag) -> str:
        verse_table = response.select_one('table table table')

        if verse_table is None:
            raise DoNotUnderstandError

        rows = verse_table.select('tr')

        if rows[0].get_text('').strip() == 'No Verses Found':
            raise DoNotUnderstandError

        for row in rows:
            cells = row.select('td')
            if len(cells) != 2 or cells[0].string == '\xa0':
                row.decompose()

        return number_re.sub(r'**\1**', verse_table.get_text(''))

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        return self.base_url

    def _get_search_results(self, response: Tag) -> SearchResults:
        verse_table = response.select_one('table table table')

        if verse_table is None:
            raise DoNotUnderstandError

        rows = verse_table.select('tr')

        if rows[0].get_text('').strip() == 'No Verses Found':
            return SearchResults([], 0)

        rows[0].decompose()
        rows[-2].decompose()
        rows[-1].decompose()

        verses = []  # type: List[VerseRange]
        chapter_string = ''

        for row in verse_table.select('tr'):
            cells = row.select('td')
            if cells[0].string == '\xa0':
                chapter_string = row.get_text('').strip()
            else:
                verse_string = cells[0].get_text('').strip()[:-1]
                verses.append(VerseRange.from_string(f'{chapter_string}:{verse_string}'))

        return SearchResults(verses[:20], len(verses))

    async def search(self, version: str, terms: List[str]) -> SearchResults:
        url = self._get_search_url(version, terms)
        response = await self.post(url, {
            'search_type': 'advanced_search',
            'parallel_1': version,
            'displayFormat': 'normalNoHeader',
            'book_section': 'ALL',
            'book': 'ALL',
            'search': ' AND '.join(terms),
            'show_commentary': '0',
            'show_context': '0',
            'show_illustrations': '0',
            'show_maps': '0'
        })
        return self._get_search_results(response)
