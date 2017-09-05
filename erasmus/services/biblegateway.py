from typing import List
from bs4 import BeautifulSoup
import re

from ..data import Passage, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError

total_re = re.compile(r'^(?P<total>\d+)')


# TODO: Error handling
class BibleGateway(Service[str]):
    async def get(self, url: str) -> str:
        async with await self._get(url) as response:
            return await response.text()

    def _get_passage_url(self, version: str, passage: Passage) -> str:
        search = str(passage).replace(' ', '+').replace(':', '%3A')
        return f'https://www.biblegateway.com/passage/?search={search}&version={version}&interface=print'

    def _get_passage_text(self, response: str) -> str:
        soup = BeautifulSoup(response, 'html.parser')

        verse_block = soup.select_one('.result-text-style-normal')

        if verse_block is None:
            raise DoNotUnderstandError

        for node in verse_block.select('h1, h3, .footnotes, .footnote, .crossrefs, .crossreference'):
            # Remove headings and footnotes
            node.decompose()
        for number in verse_block.select('span.chapternum'):
            # Replace chapter number with 1.
            number.string = '1.'
        for number in verse_block.select('sup.versenum'):
            # Add a period after verse numbers
            number.string = f'{number.string.strip()}.'

        result = ' '.join(verse_block.get_text(' ', strip=True).replace('\n', ' ').replace('  ', ' ').split())
        return result

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        quicksearch = '+'.join(terms)
        return (f'https://www.biblegateway.com/quicksearch/?quicksearch={quicksearch}&qs_version={version}&'
                'limit=20&interface=print')

    def _get_search_results(self, response: str) -> SearchResults:
        soup = BeautifulSoup(response, 'html.parser')

        verse_nodes = soup.select('.search-result-list .bible-item .bible-item-title')

        if verse_nodes is None:
            raise DoNotUnderstandError

        verses = [Passage.from_string(node.string.strip()) for node in verse_nodes]

        total_node = soup.select_one('.search-total-results')

        if total_node is None:
            raise DoNotUnderstandError

        match = total_re.match(total_node.get_text(' ', strip=True))

        if match is None:
            raise DoNotUnderstandError

        return SearchResults(verses, int(match.group('total')))
