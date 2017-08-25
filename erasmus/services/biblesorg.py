from aiohttp import BasicAuth
from bs4 import BeautifulSoup

from ..service import Service, Passage
from ..exceptions import DoNotUnderstandError

# TODO: Better error handling

class BiblesOrg(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._auth = BasicAuth(self.config.api_key, 'X')

    async def _get_passage(self, version: str, passage: str) -> str:
        url = f'https://bibles.org/v2/passages.js?q[]={passage}&version={version}'
        response = await self._get_url(url, auth=self._auth)
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

    def _parse_passage(self, passage: Passage) -> str:
        verses = f'{passage.verse_start}'
        if passage.verse_end > -1:
            verses = f'{verses}-{passage.verse_end}'

        return f'{passage.book}+{passage.chapter}:{verses}'

    async def _process_response(self, response):
        obj = await response.json()
        return obj['response']
