# Service for querying bibles.org

from typing import List, Optional, Dict, Any
from aiohttp import BasicAuth, ClientResponse
import async_timeout
from bs4 import BeautifulSoup
from botus_receptus import re
from mypy_extensions import TypedDict
from ..json import loads, get, has

from ..data import VerseRange, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError

from yarl import URL

_img_re = re.compile('src="', re.named_group('src')('[^"]+'), '"')


class PassageDict(TypedDict):
    text: str


class SummaryDict(TypedDict):
    total: int


class VerseDict(TypedDict):
    reference: str


class SearchResultDict(TypedDict):
    summary: SummaryDict
    verses: List[VerseDict]


# TODO: Better error handling
class BiblesOrg(Service[Dict[str, Any]]):
    passage_url = URL('https://bibles.org/v2/passages.js')
    search_url = URL('https://bibles.org/v2/verses.js')
    _auth: Optional[BasicAuth]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.config:
            self._auth = BasicAuth(self.config.get('api_key'), 'X')

    async def _process_response(self, response: ClientResponse) -> Dict[str, Any]:
        obj = await response.json(loads=loads, content_type=None)

        # Make a request for the image to report to the Fair Use Management System
        meta: str = get(obj, 'response.meta.fums_noscript')
        if meta:
            match = _img_re.search(meta)
            if match:
                with async_timeout.timeout(10):
                    async with self.session.get(match.group('src')) as response:
                        await response.read()

        return obj['response']

    async def get(self, url: URL, **request_options: Any) -> Dict[str, Any]:
        return await super().get(url, auth=self._auth)

    def _get_passage_url(self, version: str, verses: VerseRange) -> URL:
        return self.passage_url.with_query({
            'q[]': str(verses),
            'version': version
        })

    def _get_passage_text(self, response: Dict[str, Any]) -> str:
        passages: List[PassageDict] = get(response, 'search.result.passages')

        if passages is None or len(passages) == 0:
            raise DoNotUnderstandError

        soup = BeautifulSoup(passages[0]['text'], 'html.parser')

        for heading in soup.select('h3'):
            # Remove headings
            heading.decompose()
        for number in soup.select('sup.v'):
            # Add a period after verse numbers
            number.string = f' __BOLD__{number.string}.__BOLD__ '
        for it in soup.select('span.it'):
            it.replace_with(f'__ITALIC__{it.get_text(" ", strip=True).strip()}__ITALIC__')
        for span in soup.select('span.sc'):
            span.unwrap()
        for br in soup.select('br'):
            br.replace_with('\n')

        return soup.get_text('')

    def _get_search_url(self, version: str, terms: List[str]) -> URL:
        return self.search_url.with_query({
            'keyword': ' '.join(terms),
            'precision': 'all',
            'version': version,
            'sort_order': 'canonical',
            'limit': 20
        })

    def _get_search_results(self, response: Dict[str, Any]) -> SearchResults:
        result: SearchResultDict = get(response, 'search.result')

        if result is None:
            raise DoNotUnderstandError

        total: int = get(result, 'summary.total') or 0

        if not has(result, 'summary.total') or total > 0 and not has(result, 'verses'):
            raise DoNotUnderstandError

        if total > 0:
            verses = [VerseRange.from_string(verse['reference']) for verse in result['verses']]
        else:
            verses = []

        return SearchResults(verses, total)
