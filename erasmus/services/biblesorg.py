import asyncio
from aiohttp import BasicAuth
from bs4 import BeautifulSoup

from .service import Service
from ..exceptions import DoNotUnderstandError

class BiblesOrg(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._auth = BasicAuth(self.config.api_key, 'X')

    async def get_verse(self, version: str, book: str, chapter: int = 1, verse_min: int = 1, verse_max: int = -1) -> str:
        verses = f'{verse_min}'
        if verse_max > -1:
            verses = f'{verses}-{verse_max}'
        url = f'https://bibles.org/v2/passages.js?q[]={book}+{chapter}:{verses}&version={version}'
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

    async def _process_response(self, response):
        obj = await response.json()
        return obj['response']
