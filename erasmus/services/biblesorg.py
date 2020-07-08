# Service for querying bibles.org

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional
from typing_extensions import TypedDict

from aiohttp import BasicAuth
from attr import attrib, dataclass
from botus_receptus import re
from bs4 import BeautifulSoup
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import DoNotUnderstandError
from ..json import get, has, loads
from ..protocols import Bible
from .base_service import BaseService

_img_re = re.compile('src="', re.named_group('src')('[^"]+'), '"')


class SummaryDict(TypedDict):
    total: int


class VerseDict(TypedDict):
    reference: str
    text: str


class SearchResultDict(TypedDict):
    summary: SummaryDict
    verses: List[VerseDict]


# TODO: better error handling
@dataclass(slots=True)
class BiblesOrg(BaseService):
    _auth: Optional[BasicAuth] = attrib(init=False)
    _passage_url: URL = attrib(init=False)
    _search_url: URL = attrib(init=False)

    def __attrs_post_init__(self) -> None:
        self._passage_url = URL('https://bibles.org/v2/passages.js')
        self._search_url = URL('https://bibles.org/v2/verses.js')

        if self.config:
            self._auth = BasicAuth(
                login=self.config.get('api_key', ''), password='X', encoding='latin1'
            )

    def _transform_verse_dict(
        self, bible: Bible, verses: VerseRange, verse: VerseDict
    ) -> Passage:
        soup = BeautifulSoup(verse['text'], 'html.parser')

        for heading in soup.select('h3'):
            # Remove headings
            heading.decompose()
        for number in soup.select('sup.v'):
            # Add a period after verse numbers
            number.insert_before(' __BOLD__')
            number.insert_after('__BOLD__ ')
            number.string = f'{number.string}.'
            number.unwrap()
        for sup in soup.select('sup:not(.v)'):
            sup.decompose()
        for it in soup.select('span.it'):
            it.insert_before('__ITALIC__')
            it.insert_after('__ITALIC__')
            it.unwrap()
        for it in soup.select('em'):
            it.insert_before('__BOLD__')
            it.insert_after('__BOLD__')
            it.unwrap()
        for span in soup.select('span.sc'):
            span.unwrap()
        for br in soup.select('br'):
            br.replace_with('\n')

        text = self._replace_special_escapes(bible, soup.get_text(''))

        return Passage(text=text, range=verses, version=bible.abbr)

    @asynccontextmanager
    async def get_with_fums(
        self, url: URL, query: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        async with self.get(
            url.with_query(query), auth=self._auth, verify_ssl=False
        ) as response:
            obj = await response.json(loads=loads, content_type=None)

            # Make a request for the image to report to the Fair Use Management System
            meta: str = get(obj, 'response.meta.fums_noscript')
            if meta:
                if (match := _img_re.search(meta)) is not None:
                    try:
                        async with self.get(match.group('src')) as fums_response:
                            await fums_response.read()
                    except asyncio.TimeoutError:
                        pass

            yield obj['response']

    @asynccontextmanager
    async def _request_passage(
        self, bible: Bible, verses: VerseRange
    ) -> AsyncIterator[Passage]:
        async with self.get_with_fums(
            self._passage_url, {'q[]': str(verses), 'version': bible.service_version}
        ) as response:
            passage: VerseDict = get(response, 'search.result.passages.0')

            if passage is None:
                raise DoNotUnderstandError

            yield self._transform_verse_dict(bible, verses, passage)

    @asynccontextmanager
    async def _request_search(
        self, bible: Bible, terms: List[str], *, limit: int, offset: int
    ) -> AsyncIterator[SearchResults]:
        async with self.get_with_fums(
            self._search_url,
            {
                'keyword': ' '.join(terms),
                'precision': 'all',
                'version': bible.service_version,
                'sort_order': 'canonical',
                'limit': limit,
                'offset': offset,
            },
        ) as response:
            result: SearchResultDict = get(response, 'search.result')

            if result is None:
                raise DoNotUnderstandError

            total: int = get(result, 'summary.total') or 0

            if (
                not has(result, 'summary.total')
                or total > 0
                and not has(result, 'verses')
            ):
                raise DoNotUnderstandError

            def mapper(verse_dict: VerseDict) -> Passage:
                verse = VerseRange.from_string(verse_dict['reference'])

                return self._transform_verse_dict(bible, verse, verse_dict)

            passages = list(map(mapper, result['verses'])) if total > 0 else []

            yield SearchResults(passages, total)
