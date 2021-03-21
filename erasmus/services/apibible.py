from __future__ import annotations

import asyncio
from typing import Any, Final, TypedDict

import aiohttp
from attr import attrib, dataclass
from botus_receptus import re
from bs4 import BeautifulSoup
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import DoNotUnderstandError
from ..json import get, loads
from ..protocols import Bible
from .base_service import BaseService

_img_re: Final = re.compile('src="', re.named_group('src')('[^"]+'), '"')
_book_map: Final[dict[str, str]] = {
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


class _ResponseMetaDict(TypedDict):
    fumsNoScript: str | None


class _ResponseDict(TypedDict):
    data: dict[str, Any]
    meta: _ResponseMetaDict | None


@dataclass(slots=True)
class ApiBible(BaseService):
    _passage_url: URL = attrib(init=False)
    _search_url: URL = attrib(init=False)
    _headers: dict[str, str] = attrib(init=False)

    def __attrs_post_init__(self, /) -> None:
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

    def __get_passage_id(self, verses: VerseRange, /) -> str:
        book_id: str = _book_map[verses.book]
        passage_id: str = f'{book_id}.{verses.start.chapter}.{verses.start.verse}'

        if verses.end is not None:
            passage_id = (
                f'{passage_id}-{book_id}.{verses.end.chapter}.{verses.end.verse}'
            )

        return passage_id

    def __transform_verse(
        self,
        bible: Bible,
        verses: VerseRange,
        content: str,
        /,
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

        text = self.replace_special_escapes(bible, soup.get_text(''))

        return Passage(text=text, range=verses, version=bible.abbr)

    async def __process_response(
        self,
        response: aiohttp.ClientResponse,
        /,
    ) -> dict[str, Any]:
        if response.status != 200:
            raise DoNotUnderstandError

        json: _ResponseDict = await response.json(loads=loads, content_type=None)

        # Make a request for the image to report to the Fair Use Management System
        meta: str | None = get(json, 'meta.fumsNoScript')
        if meta:
            if (match := _img_re.search(meta)) is not None:
                try:
                    async with self.session.get(match.group('src')) as fums_response:
                        await fums_response.read()
                except asyncio.TimeoutError:
                    pass

        return json['data']

    async def get_passage(self, bible: Bible, verses: VerseRange, /) -> Passage:
        async with self.session.get(
            self._passage_url.with_path(
                self._passage_url.path.format(
                    bibleId=bible.service_version,
                    passageId=self.__get_passage_id(verses),
                )
            ).with_query(
                {
                    'include-notes': 'false',
                    'include-titles': 'false',
                    'include-chapter-numbers': 'false',
                    'include-verse-numbers': 'true',
                }
            )
        ) as response:
            data = await self.__process_response(response)

            return self.__transform_verse(bible, verses, data['content'])

    async def search(
        self,
        bible: Bible,
        terms: list[str],
        /,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResults:
        async with self.session.get(
            self._search_url.with_path(
                self._search_url.path.format(bibleId=bible.service_version)
            ).with_query(
                {
                    'query': ' '.join(terms),
                    'limit': limit,
                    'offset': offset,
                    'sort': 'canonical',
                }
            )
        ) as response:
            data = await self.__process_response(response)

            total: int = get(data, 'total') or 0

            passages = [
                Passage(
                    text=self.replace_special_escapes(bible, verse['text']),
                    range=VerseRange.from_string(verse['reference']),
                    version=bible.abbr,
                )
                for verse in get(data, 'verses', [])
            ]

            return SearchResults(passages, total)
