import pytest
from pathlib import Path
from . import ServiceTest

from erasmus.services import BibleGateway
from erasmus.data import VerseRange

__directory__ = Path(__file__).resolve().parent

passage_sources = {
    'Galatians 3:10-11': (__directory__ / 'biblegateway_Galatians_3:10-11_NASB.txt').read_text(),
    'Mark 5:1': (__directory__ / 'biblegateway_Mark_5:1_NASB.txt').read_text(),
    'Psalm 32:1-5': (__directory__ / 'biblegateway_Psalm_32:1-5_ESV.txt').read_text()
}


class TestBibleGateway(ServiceTest):
    @pytest.fixture
    def service(self, mock_client_session):
        return BibleGateway({}, mock_client_session)

    @pytest.fixture
    def mock_search(self, mocker, mock_response):
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
    def mock_search_failure(self, mocker, mock_search):
        mock_search.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return mock_search

    @pytest.fixture
    def search_url(self):
        return f'https://www.biblegateway.com/quicksearch/?quicksearch=one+two+three&qs_version=eng-BIB&' \
               'limit=20&interface=print'

    @pytest.fixture
    def mock_passage(self, request, mocker, mock_response):
        if hasattr(request, 'param'):
            text = passage_sources[request.param]
        else:
            text = ''

        mocker.patch.object(mock_response, 'text',
                            new_callable=mocker.AsyncMock,
                            return_value=text)

        return mock_response

    @pytest.fixture
    def mock_passage_failure(self, mocker, mock_passage):
        mock_passage.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return mock_passage

    def get_passages_url(self, version: str, verses: VerseRange) -> str:
        passage_str = str(verses).replace(' ', '+').replace(':', '%3A')
        return f'https://www.biblegateway.com/passage/?search={passage_str}&version={version}&interface=print'
