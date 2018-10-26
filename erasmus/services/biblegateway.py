# Service for querying biblegateway.com

from __future__ import annotations

from typing import List
from bs4 import BeautifulSoup, Tag
from aiohttp import ClientResponse
from botus_receptus import re

from ..data import VerseRange, SearchResults
from ..service import Service
from ..exceptions import DoNotUnderstandError

from yarl import URL

total_re = re.compile(re.START, re.named_group('total')(re.one_or_more(re.DIGITS)))


# TODO: Error handling
class BibleGateway(Service[Tag]):
    passage_url = URL('https://www.biblegateway.com/passage/')
    search_url = URL('https://www.biblegateway.com/quicksearch/')

    async def _process_response(self, response: ClientResponse) -> Tag:
        text = await response.text()
        return BeautifulSoup(text, 'html.parser')

    def _get_passage_url(self, version: str, verses: VerseRange) -> URL:
        return self.passage_url.with_query(
            {'search': str(verses), 'version': version, 'interface': 'print'}
        )

    def _get_passage_text(self, response: Tag) -> str:
        verse_block = response.select_one(
            '.result-text-style-normal, .result-text-style-rtl'
        )

        if verse_block is None:
            raise DoNotUnderstandError

        for node in verse_block.select(
            'h1, h3, .footnotes, .footnote, .crossrefs, .crossreference'
        ):
            # Remove headings and footnotes
            node.decompose()
        for number in verse_block.select('span.chapternum'):
            number.string = '__BOLD__1.__BOLD__ '
        for small_caps in verse_block.select('.small-caps'):
            small_caps.string = small_caps.string.upper()
        for number in verse_block.select('sup.versenum'):
            # Add a period after verse numbers
            number.string = f'__BOLD__{number.string.strip()}.__BOLD__ '
        for br in verse_block.select('br'):
            br.replace_with('\n')
        for h4 in verse_block.select('h4'):
            h4.replace_with(f'__BOLD__{h4.get_text(" ", strip=True).strip()}__BOLD__ ')
        for italic in verse_block.select('.selah, i'):
            italic.replace_with(
                f'__ITALIC__{italic.get_text(" ", strip=True).strip()}__ITALIC__'
            )

        return verse_block.get_text('')

    def _get_search_url(self, version: str, terms: List[str]) -> URL:
        return self.search_url.with_query(
            {
                'quicksearch': ' '.join(terms),
                'qs_version': version,
                'limit': 20,
                'interface': 'print',
            }
        )

    def _get_search_results(self, response: Tag) -> SearchResults:
        verse_nodes = response.select(
            '.search-result-list .bible-item .bible-item-title'
        )

        if verse_nodes is None:
            raise DoNotUnderstandError

        verses = [VerseRange.from_string(node.string.strip()) for node in verse_nodes]

        total_node = response.select_one('.search-total-results')

        if total_node is None:
            raise DoNotUnderstandError

        match = total_re.match(total_node.get_text(' ', strip=True))

        if match is None:
            raise DoNotUnderstandError

        return SearchResults(verses, int(match.group('total')))
