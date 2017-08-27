from typing import List
from bs4 import BeautifulSoup
import re

from ..service import Service, Passage, SearchResults

# TODO: Error handling

total_re = re.compile(r'^(?P<total>\d+)')

class BibleGateway(Service):
    async def search(self, version: str, terms: List[str]) -> SearchResults:
        quicksearch = '+'.join(terms)
        url = f'https://www.biblegateway.com/quicksearch/?quicksearch={quicksearch}&qs_version={version}&limit=20&interface=print'
        response = await self._get_url(url)

        soup = BeautifulSoup(response, 'html.parser')

        verse_nodes = soup.select('.search-result-list .bible-item .bible-item-title')
        verses = [ Passage.from_string(node.string) for node in verse_nodes ]

        total_node = soup.select_one('.search-total-results')
        match = total_re.match(total_node.get_text(' ', strip=True))

        return SearchResults(verses, int(match.group('total')))

    async def _get_passage(self, version: str, passage: str) -> str:
        url = f'https://www.biblegateway.com/passage/?search={passage}&version={version}&interface=print'
        response = await self._get_url(url)

        soup = BeautifulSoup(response, 'html.parser')

        verse_block = soup.select_one('.result-text-style-normal')

        for node in verse_block.select('h1, h3, .footnotes, .footnote, .crossrefs, .crossreference'):
            # Remove headings and footnotes
            node.decompose()
        for number in verse_block.select('span.chapternum'):
            # Replace chapter number with 1.
            number.string = '1.'
        for number in verse_block.select('sup.versenum'):
            # Add a period after verse numbers
            number.string = f'{number.string.strip()}.'

        result = verse_block.get_text(' ', strip=True).replace('\n', ' ').replace('  ', ' ')
        return result

    def _parse_passage(self, passage: Passage) -> str:
        verses = f'{passage.verse_start}'
        if passage.verse_end > -1:
            verses = f'{verses}-{passage.verse_end}'

        return f'{passage.book.replace(" ", "+")}+{passage.chapter}%3A{verses}'

    async def _process_response(self, response):
        return await response.text()
