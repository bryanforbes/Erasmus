from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, Final, TypedDict

import orjson
from attrs import define, field
from botus_receptus import re
from bs4 import BeautifulSoup
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import BookNotInVersionError, DoNotUnderstandError
from ..json import get
from .base_service import BaseService

if TYPE_CHECKING:
    import aiohttp

    from ..types import Bible

_img_re: Final = re.compile('src="', re.named_group('src')('[^"]+'), '"')


class _ResponseMetaDict(TypedDict):
    fumsNoScript: str | None


class _ResponseDict(TypedDict):
    data: dict[str, Any]
    meta: _ResponseMetaDict | None


@define
class ApiBible(BaseService):
    _passage_url: URL = field(init=False)
    _search_url: URL = field(init=False)
    _headers: dict[str, str] = field(init=False)

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
        if verses.paratext is None:
            raise BookNotInVersionError(verses.book, verses.version or 'default')

        passage_id: str = (
            f'{verses.paratext}.{verses.start.chapter}.{verses.start.verse}'
        )

        if verses.end is not None:
            passage_id = (
                f'{passage_id}-{verses.paratext}.'
                f'{verses.end.chapter}.{verses.end.verse}'
            )

        return passage_id

    def __transform_verse(
        self, bible: Bible, verses: VerseRange, content: str, /
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
        self, response: aiohttp.ClientResponse, /
    ) -> dict[str, Any]:
        if response.status != 200:
            raise DoNotUnderstandError()

        json: _ResponseDict = await response.json(loads=orjson.loads, content_type=None)

        # Make a request for the image to report to the Fair Use Management System
        meta: str | None = get(json, 'meta.fumsNoScript')
        if meta and (match := _img_re.search(meta)) is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                async with self.session.get(match.group('src')) as fums_response:
                    await fums_response.read()

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
            ),
            headers=self._headers,
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
            ),
            headers=self._headers,
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
