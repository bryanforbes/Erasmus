# Service for querying bibles.org

from typing import List, cast, Optional
from aiohttp import BasicAuth, ClientResponse
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from configparser import SectionProxy
from ..json import loads, JSONObject

from ..data import VerseRange, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError


# TODO: Better error handling
class BiblesOrg(Service[JSONObject]):
    base_url = 'https://bibles.org/v2'

    def __init__(self, config: Optional[SectionProxy]) -> None:
        super().__init__(config)

        self._auth = BasicAuth(self.config.get('api_key'), 'X')

    async def _process_response(self, response: ClientResponse) -> JSONObject:
        obj = cast(JSONObject, await response.json(loads=loads, content_type='application/javascript'))
        return obj.response

    async def get(self, url: str, **session_options) -> JSONObject:
        return await super().get(url, auth=self._auth)

    def _get_passage_url(self, version: str, verses: VerseRange) -> str:
        return f'{self.base_url}/passages.js?' + urlencode({
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
            number.string = f' **{number.string}.** '
        for span in soup.select('span.sc'):
            span.unwrap()

        return soup.get_text('')

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        return f'{self.base_url}/verses.js?' + urlencode({
            'keyword': ' '.join(terms),
            'precision': 'all',
            'version': version,
            'sort_order': 'canonical',
            'limit': 20
        })

    def _get_search_results(self, response: JSONObject) -> SearchResults:
        result = response.get('search.result')

        if result is None or 'summary' not in result or 'total' not in result.summary or \
                result.summary.total > 0 and 'verses' not in result:
            raise DoNotUnderstandError

        if result.summary.total > 0:
            verses = [VerseRange.from_string(verse.reference) for verse in result.verses]
        else:
            verses = []

        return SearchResults(verses, result.summary.total)
