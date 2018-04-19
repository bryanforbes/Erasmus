# Service for querying bibles.org

from typing import List, cast, Optional, Any
from aiohttp import BasicAuth, ClientResponse
import async_timeout
from bs4 import BeautifulSoup
from ..json import loads, JSONObject
from .. import re

from ..data import VerseRange, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError

from yarl import URL

_img_re = re.compile('src="', re.named_group('src')('[^"]+'), '"')


# TODO: Better error handling
class BiblesOrg(Service[JSONObject]):
    passage_url = URL('https://bibles.org/v2/passages.js')
    search_url = URL('https://bibles.org/v2/verses.js')
    _auth: Optional[BasicAuth]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.config:
            self._auth = BasicAuth(self.config.get('api_key'), 'X')

    async def _process_response(self, response: ClientResponse) -> JSONObject:
        obj = cast(JSONObject, await response.json(loads=loads, content_type=None))

        # Make a request for the image to report to the Fair Use Management System
        meta: str = obj.get('response.meta.fums_noscript')
        if meta:
            match = _img_re.search(meta)
            if match:
                with async_timeout.timeout(10):
                    async with self.session.get(match.group('src')) as response:
                        await response.read()

        return obj.response

    async def get(self, url: URL, **request_options: Any) -> JSONObject:
        return await super().get(url, auth=self._auth)

    def _get_passage_url(self, version: str, verses: VerseRange) -> URL:
        return self.passage_url.with_query({
            'q[]': str(verses),
            'version': version
        })

    def _get_passage_text(self, response: JSONObject) -> str:
        passages = response.get('search.result.passages')

        if passages is None or len(passages) == 0:
            raise DoNotUnderstandError

        soup = BeautifulSoup(passages[0].text, 'html.parser')

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

    def _get_search_results(self, response: JSONObject) -> SearchResults:
        result: JSONObject = response.get('search.result')

        if result is None:
            raise DoNotUnderstandError

        total: int = result.get('summary.total') or 0

        if not result.has('summary.total') or total > 0 and not result.has('verses'):
            raise DoNotUnderstandError

        if total > 0:
            verses = [VerseRange.from_string(verse.reference) for verse in result.verses]
        else:
            verses = []

        return SearchResults(verses, total)
