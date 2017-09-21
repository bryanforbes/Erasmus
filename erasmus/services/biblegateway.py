from typing import List
from bs4 import BeautifulSoup, Tag
from aiohttp import ClientResponse
from urllib.parse import urlencode
import re

from ..data import Passage, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError

total_re = re.compile(r'^(?P<total>\d+)')


# TODO: Error handling
class BibleGateway(Service[Tag]):
    base_url = 'https://www.biblegateway.com'

    async def _process_response(self, response: ClientResponse) -> Tag:
        text = await response.text()
        return BeautifulSoup(text, 'html.parser')

    def _get_passage_url(self, version: str, passage: Passage) -> str:
        return f'{self.base_url}/passage/?' + urlencode({
            'search': str(passage),
            'version': version,
            'interface': 'print'
        })

    # TODO: Handle RTL text better
    def _get_passage_text(self, response: Tag) -> str:
        verse_block = response.select_one('.result-text-style-normal, .result-text-style-rtl')

        if verse_block is None:
            raise DoNotUnderstandError

        for node in verse_block.select('h1, h3, .footnotes, .footnote, .crossrefs, .crossreference'):
            # Remove headings and footnotes
            node.decompose()
        for number in verse_block.select('span.chapternum'):
            # Replace chapter number with 1.
            number.string = '1. '
        for small_caps in verse_block.select('.small-caps'):
            small_caps.string = small_caps.string.upper()
        for number in verse_block.select('sup.versenum'):
            # Add a period after verse numbers
            number.string = f'{number.string.strip()}. '

        result = (' '.join(verse_block.get_text('').replace('\n', ' ').split())).strip()
        return result

    def _get_search_url(self, version: str, terms: List[str]) -> str:
        return f'{self.base_url}/quicksearch/?' + urlencode({
            'quicksearch': ' '.join(terms),
            'qs_version': version,
            'limit': 20,
            'interface': 'print'
        })

    def _get_search_results(self, response: Tag) -> SearchResults:
        verse_nodes = response.select('.search-result-list .bible-item .bible-item-title')

        if verse_nodes is None:
            raise DoNotUnderstandError

        verses = [Passage.from_string(node.string.strip()) for node in verse_nodes]

        total_node = response.select_one('.search-total-results')

        if total_node is None:
            raise DoNotUnderstandError

        match = total_re.match(total_node.get_text(' ', strip=True))

        if match is None:
            raise DoNotUnderstandError

        return SearchResults(verses, int(match.group('total')))
