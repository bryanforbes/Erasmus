from __future__ import annotations

import asyncio

from typing import Any, List, Dict, AsyncIterator
from attr import dataclass, attrib
from botus_receptus import re
from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from yarl import URL

from .base_service import BaseService
from ..data import Passage, VerseRange, SearchResults
from ..exceptions import DoNotUnderstandError
from ..json import loads, get
from ..protocols import Bible


_img_re = re.compile('src="', re.named_group('src')('[^"]+'), '"')


book_map: Dict[str, str] = {
    'Genesis': 'GEN',
    'Exodus': 'EXO',
    'Leviticus': 'LEV',
    'Numbers': 'NUM',
    'Deuteronomy': 'DEU',
    'Joshua': 'JOS',
    'Judges': 'JDG',
    'Ruth': 'RUT',
    '1 Samuel': '1SA',
    '2 Samuel': '2SA',
    '1 Kings': '1KI',
    '2 Kings': '2KI',
    '1 Chronicles': '1CH',
    '2 Chronicles': '2CH',
    'Ezra': 'EZR',
    'Nehemiah': 'NEH',
    'Esther': 'EST',
    'Job': 'JOB',
    'Psalm': 'PSA',
    'Proverbs': 'PRO',
    'Ecclesiastes': 'ECC',
    'Song of Solomon': 'SNG',
    'Isaiah': 'ISA',
    'Jeremiah': 'JER',
    'Lamentations': 'LAM',
    'Ezekiel': 'EZK',
    'Daniel': 'DAN',
    'Hosea': 'HOS',
    'Joel': 'JOL',
    'Amos': 'AMO',
    'Obadiah': 'OBA',
    'Jonah': 'JON',
    'Micah': 'MIC',
    'Nahum': 'NAM',
    'Habakkuk': 'HAB',
    'Zephaniah': 'ZEP',
    'Haggai': 'HAG',
    'Zechariah': 'ZEC',
    'Malachi': 'MAL',
    '1 Esdras': '1ES',
    '2 Esdras': '2ES',
    'Tobit': 'TOB',
    'Judith': 'JDT',
    'Additions to Esther': 'ESG',
    'Wisdom': 'WIS',
    'Sirach': 'SIR',
    'Baruch': 'BAR',
    'Prayer of Azariah': 'S3Y',
    'Susanna': 'SUS',
    'Bel and the Dragon': 'BEL',
    'Prayer of Manasseh': 'MAN',
    '1 Maccabees': '1MA',
    '2 Maccabees': '2MA',
    'Matthew': 'MAT',
    'Mark': 'MRK',
    'Luke': 'LUK',
    'John': 'JHN',
    'Acts': 'ACT',
    'Romans': 'ROM',
    '1 Corinthians': '1CO',
    '2 Corinthians': '2CO',
    'Galatians': 'GAL',
    'Ephesians': 'EPH',
    'Philippians': 'PHP',
    'Colossians': 'COL',
    '1 Thessalonians': '1TH',
    '2 Thessalonians': '2TH',
    '1 Timothy': '1TI',
    '2 Timothy': '2TI',
    'Titus': 'TIT',
    'Philemon': 'PHM',
    'Hebrews': 'HEB',
    'James': 'JAS',
    '1 Peter': '1PE',
    '2 Peter': '2PE',
    '1 John': '1JN',
    '2 John': '2JN',
    '3 John': '3JN',
    'Jude': 'JUD',
    'Revelation': 'REV',
}


@dataclass(slots=True)
class ApiBible(BaseService):
    _passage_url: URL = attrib(init=False)
    _search_url: URL = attrib(init=False)
    _headers: Dict[str, str] = attrib(init=False)

    def __attrs_post_init__(self) -> None:
        self._passage_url = URL(
            'https://api.scripture.api.bible/v1/bibles/{bibleId}/passages/{passageId}'
        )
        self._search_url = URL(
            'https://api.scripture.api.bible/v1/bibles/{bibleId}/search'
        )

        if self.config:
            self._headers = {'api-key': self.config.get('api_key', '')}
        else:
            self._headers = {}

    def _transform_verse_dict(
        self, bible: Bible, verses: VerseRange, content: str
    ) -> Passage:
        soup = BeautifulSoup(content, 'html.parser')

        for number in soup.select('span.v'):
            # Add a period after verse numbers
            number.insert_before(' __BOLD__')
            number.insert_after('__BOLD__ ')
            number.string = f'{number.string}.'
            number.unwrap()
        for it in soup.select('span.add'):
            it.insert_before('__ITALIC__')
            it.insert_after('__ITALIC__')
            it.unwrap()
        for br in soup.select('br'):
            br.replace_with('\n')

        text = self._replace_special_escapes(bible, soup.get_text(''))

        return Passage(text=text, range=verses, version=bible.abbr)

    def _get_passage_id(self, verses: VerseRange) -> str:
        book_id: str = book_map[verses.book]
        passage_id: str = f'{book_id}.{verses.start.chapter}.{verses.start.verse}'

        if verses.end is not None:
            passage_id = (
                f'{passage_id}-{book_id}.{verses.end.chapter}.{verses.end.verse}'
            )

        return passage_id

    @asynccontextmanager
    async def get_with_fums(
        self, url: URL, query: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        async with self.get(url.with_query(query), headers=self._headers) as response:
            if response.status != 200:
                raise DoNotUnderstandError

            obj = await response.json(loads=loads, content_type=None)

            # Make a request for the image to report to the Fair Use Management System
            meta: str = get(obj, 'meta.fumsNoScript')
            if meta:
                match = _img_re.search(meta)
                if match:
                    try:
                        async with self.get(match.group('src')) as fums_response:
                            await fums_response.read()
                    except asyncio.TimeoutError:
                        pass

            yield obj['data']

    @asynccontextmanager
    async def _request_passage(
        self, bible: Bible, verses: VerseRange
    ) -> AsyncIterator[Passage]:
        async with self.get_with_fums(
            self._passage_url.with_path(
                self._passage_url.path.format(
                    bibleId=bible.service_version,
                    passageId=self._get_passage_id(verses),
                )
            ),
            {
                'include-notes': 'false',
                'include-titles': 'false',
                'include-chapter-numbers': 'false',
                'include-verse-numbers': 'true',
            },
        ) as response:
            yield self._transform_verse_dict(bible, verses, response['content'])

    @asynccontextmanager
    async def _request_search(
        self, bible: Bible, terms: List[str], *, limit: int, offset: int
    ) -> AsyncIterator[SearchResults]:
        async with self.get_with_fums(
            self._search_url.with_path(
                self._search_url.path.format(bibleId=bible.service_version)
            ),
            {
                'query': ' '.join(terms),
                'limit': limit,
                'offset': offset,
                'sort': 'canonical',
            },
        ) as response:
            total: int = get(response, 'total') or 0

            passages = [
                Passage(
                    text=self._replace_special_escapes(bible, verse['text']),
                    range=VerseRange.from_string(verse['reference']),
                    version=bible.abbr,
                )
                for verse in get(response, 'verses', [])
            ]

            yield SearchResults(passages, total)
