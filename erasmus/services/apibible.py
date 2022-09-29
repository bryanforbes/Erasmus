from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final, Literal, TypedDict

import orjson
from attrs import define, field
from botus_receptus import re
from yarl import URL

from ..data import Passage, SearchResults, VerseRange
from ..exceptions import BookNotInVersionError, DoNotUnderstandError
from ..json import get
from .base_service import BaseService

if TYPE_CHECKING:
    from typing_extensions import Self

    import aiohttp

    from ..config import ServiceConfig
    from ..types import Bible

_img_re: Final = re.compile('src="', re.named_group('src')('[^"]+'), '"')


class _Text(TypedDict):
    type: Literal['text']
    text: str


class _CharAttrs(TypedDict):
    style: Literal['add', 'wj']


class _Char(TypedDict):
    name: Literal['char']
    type: Literal['tag']
    attrs: _CharAttrs
    items: list[_Text]


class _VerseNumberAttrs(TypedDict):
    style: Literal['v']


class _VerseNumber(TypedDict):
    name: Literal['verse']
    type: Literal['tag']
    attrs: _VerseNumberAttrs
    items: list[_Text]


class _Paragraph(TypedDict):
    name: Literal['para']
    type: Literal['tag']
    items: list[_Text | _Char | _VerseNumber]


class _Meta(TypedDict):
    fumsNoScript: str | None


class _Data(TypedDict):
    content: list[_Paragraph]


class _Response(TypedDict):
    data: _Data
    meta: _Meta | None


@define(frozen=True)
class ApiBible(BaseService):
    headers: dict[str, str]
    _passage_url: URL = field(
        init=False,
        factory=lambda: URL(
            'https://api.scripture.api.bible/v1/bibles/{bibleId}/passages/{passageId}'
        ),
    )
    _search_url: URL = field(
        init=False,
        factory=lambda: URL(
            'https://api.scripture.api.bible/v1/bibles/{bibleId}/search'
        ),
    )

    def __get_passage_id(self, bible: Bible, verses: VerseRange, /) -> str:
        mapped_verses = verses.for_bible(bible)

        if mapped_verses.paratext is None:
            raise BookNotInVersionError(verses.book.name, verses.version or 'default')

        passage_id: str = (
            f'{mapped_verses.paratext}.'
            f'{mapped_verses.start.chapter}.{mapped_verses.start.verse}'
        )

        if mapped_verses.end is not None:
            passage_id = (
                f'{passage_id}-{mapped_verses.paratext}.'
                f'{mapped_verses.end.chapter}.{mapped_verses.end.verse}'
            )

        return passage_id

    def __transform_item(
        self, item: _Paragraph | _VerseNumber | _Char | _Text, strings: list[str], /
    ) -> None:
        match item:
            case {'type': 'text', 'text': text}:
                strings.append(text)
            case {'name': 'para', 'items': items}:
                for child_item in items:
                    self.__transform_item(child_item, strings)
            case {'name': 'char' | 'verse', 'attrs': attrs, 'items': items}:
                if attrs['style'] == 'add':
                    strings.append(' __ITALIC__')
                elif attrs['style'] == 'v':
                    strings.append(' __BOLD__')

                for child_item in items:
                    self.__transform_item(child_item, strings)

                if attrs['style'] == 'add':
                    strings.append('__ITALIC__ ')
                elif attrs['style'] == 'v':
                    strings.append('.__BOLD__ ')
            case _:
                pass

    def __transform_verse(
        self, bible: Bible, verses: VerseRange, content: list[_Paragraph], /
    ) -> Passage:
        strings: list[str] = []

        for paragraph in content:
            self.__transform_item(paragraph, strings)

        text = self.replace_special_escapes(bible, ''.join(strings).strip())

        return Passage(text=text, range=verses, version=bible.abbr)

    async def __process_response(self, response: aiohttp.ClientResponse, /) -> _Data:
        if response.status != 200:
            raise DoNotUnderstandError()

        json: _Response = await response.json(loads=orjson.loads, content_type=None)

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
                    passageId=self.__get_passage_id(bible, verses),
                )
            ).with_query(
                {
                    'content-type': 'json',
                    'include-notes': 'false',
                    'include-titles': 'false',
                    'include-chapter-numbers': 'false',
                    'include-verse-numbers': 'true',
                }
            ),
            headers=self.headers,
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
            headers=self.headers,
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

    @classmethod
    def from_config(
        cls, config: ServiceConfig | None, session: aiohttp.ClientSession, /
    ) -> Self:
        if config:
            headers = {'api-key': config.get('api_key', '')}
        else:
            headers = {}

        return cls(session, config, headers)
