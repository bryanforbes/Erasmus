from typing import List, cast
from aiohttp import BasicAuth, ClientResponse
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from types import SimpleNamespace
import json

from ..config import ConfigObject
from ..data import Passage, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError


def loads(s: str):
    return json.loads(s, object_hook=lambda d: SimpleNamespace(**d))


# TODO: Better error handling
class BiblesOrg(Service[SimpleNamespace]):
    base_url = 'https://bibles.org/v2'

    def __init__(self, config: ConfigObject) -> None:
        super().__init__(config)

        self._auth = BasicAuth(self.config.api_key, 'X')

    async def _process_response(self, response: ClientResponse) -> SimpleNamespace:
        obj = cast(SimpleNamespace, await response.json(loads=loads))
        return obj.response

    async def get(self, url: str, **session_options) -> SimpleNamespace:
        return await super().get(url, auth=self._auth)

    def _get_passage_url(self, version: str, passage: Passage) -> str:
        return f'{self.base_url}/passages.js?' + urlencode({
            'q[]': str(passage),
            'version': version
        })

    def _get_passage_text(self, response: SimpleNamespace) -> str:
        try:
            passages = response.search.result.passages
        except:
            raise DoNotUnderstandError
        else:
            if passages is None or len(passages) == 0:
                raise DoNotUnderstandError

        soup = BeautifulSoup(passages[0].text, 'html.parser')

        for heading in soup.select('h3'):
            # Remove headings
            heading.decompose()
        for number in soup.select('sup.v'):
            # Add a period after verse numbers
            number.string = f' {number.string}. '
        for span in soup.select('span.sc'):
            span.unwrap()

        return soup.get_text('').replace('\n', ' ').strip()

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        return f'{self.base_url}/verses.js?' + urlencode({
            'keyword': ' '.join(terms),
            'precision': 'all',
            'version': version,
            'sort_order': 'canonical',
            'limit': 20
        })

    def _get_search_results(self, response: SimpleNamespace) -> SearchResults:
        try:
            result = response.search.result
        except:
            raise DoNotUnderstandError
        else:
            if result is None or not hasattr(result, 'summary') or not hasattr(result, 'verses'):
                raise DoNotUnderstandError

        verses = [Passage.from_string(verse.reference) for verse in result.verses]

        return SearchResults(verses, result.summary.total)
