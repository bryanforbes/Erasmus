import pytest
from . import ServiceTest

from erasmus.services import BibleGateway
from erasmus.data import Passage


class TestBibleGateway(ServiceTest):
    @pytest.fixture
    def service(self):
        return BibleGateway({})

    @pytest.fixture
    def good_mock_search(self, mocker, mock_response):
        return_value = '''<html><body>
    <div id="serp-bible-pane" class="iv-pane active">
        <p class="search-total-results">
            50 Bible results for <span class="search-term">&ldquo;one two three&rdquo;</span> Showing results 1-2.
        </p>
        <h4 class="search-result-heading">
            Bible search results
        </h4>
        <div class="search-result-list">
            <div class="text-html">
                <article class="row bible-item">
                    <div class="bible-item-title-wrap col-sm-3">
                        <a class="bible-item-title" href="">John 1:1-4</a>
                    </div>
                    <div class="bible-item-text col-sm-9">Lorem ipsum</div>
                </article>
                <article class="row bible-item">
                    <div class="bible-item-title-wrap col-sm-3">
                        <a class="bible-item-title" href="">Genesis 50:1</a>
                    </div>
                    <div class="bible-item-text col-sm-9">Lorem ipsum</div>
                </article>
            </div>
        </div>
    </div>
</body></html>'''
        mocker.patch.object(mock_response, 'text',
                            new_callable=mocker.AsyncMock,
                            return_value=return_value)

        return mock_response

    @pytest.fixture
    def bad_mock_search(self, mocker, good_mock_search):
        good_mock_search.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return good_mock_search

    @pytest.fixture
    def search_url(self):
        return f'https://www.biblegateway.com/quicksearch/?quicksearch=one+two+three&qs_version=esv&' \
               'limit=20&interface=print'

    @pytest.fixture
    def good_mock_passages(self, mocker, mock_response):
        return_value = '''<html>
    <body>
        <div class="result-text-style-normal">
            <h1>This will be gone</h1>
            <h3>This will be gone too</h3>
            <div class="footnotes">
                This should be gone too
            </div>
            <div class="crossrefs">
                This should be gone as well
            </div>
            <p class="chapter-1">
                <span><span class="chapternum">5 </span>This is the
                    <sup class="crossreference">A</sup>text</span>
                <span><sup class="versenum">2 </sup>This
                is <sup class="footnote">a</sup> also the text</span>
            </p>
        </div>
    </body>
</html>'''

        mocker.patch.object(mock_response, 'text',
                            new_callable=mocker.AsyncMock,
                            return_value=return_value)

        return mock_response

    @pytest.fixture
    def bad_mock_passages(self, mocker, good_mock_passages):
        good_mock_passages.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return good_mock_passages

    def get_passages_url(self, version: str, passage: Passage) -> str:
        passage_str = str(passage).replace(' ', '+').replace(':', '%3A')
        return f'https://www.biblegateway.com/passage/?search={passage_str}&version={version}&interface=print'
