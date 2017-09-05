from typing import List, Any, Dict
from aiohttp import BasicAuth, ClientResponse
from bs4 import BeautifulSoup

from ..config import ConfigObject
from ..data import Passage, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError


# TODO: Better error handling
class BiblesOrg(Service[Dict[str, Any]]):
    base_url = 'https://bibles.org/v2'

    def __init__(self, config: ConfigObject) -> None:
        super().__init__(config)

        self._auth = BasicAuth(self.config.api_key, 'X')

    async def _process_response(self, response: ClientResponse) -> Dict[str, Any]:
        obj = await response.json()
        return obj['response']

    async def get(self, url: str, **session_options) -> Dict[str, Any]:
        return await super().get(url, auth=self._auth)

    def _get_passage_url(self, version: str, passage: Passage) -> str:
        query = str(passage).replace(' ', '+')
        return f'{self.base_url}/passages.js?q[]={query}&version={version}'

    def _get_passage_text(self, response: Dict[str, Any]) -> str:
        passages = response.get('search', {}).get('result', {}).get('passages')

        if passages is None or len(passages) == 0:
            raise DoNotUnderstandError

        soup = BeautifulSoup(passages[0]['text'], 'html.parser')

        for heading in soup.select('h3'):
            # Remove headings
            heading.decompose()
        for number in soup.select('sup.v'):
            # Add a period after verse numbers
            number.string = f'{number.string}.'

        return soup.get_text(' ', strip=True).replace('\n', ' ').replace('  ', ' ')

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        keyword = '+'.join(terms)
        return (f'{self.base_url}/verses.js?keyword={keyword}&precision=all&version={version}&'
                'sort_order=canonical&limit=20')

    def _get_search_results(self, response: Dict[str, Any]) -> SearchResults:
        result = response.get('search', {}).get('result')

        if result is None or 'summary' not in result or 'verses' not in result:
            raise DoNotUnderstandError

        verses = [Passage.from_string(verse['reference']) for verse in result['verses']]

        return SearchResults(verses, result['summary']['total'])
