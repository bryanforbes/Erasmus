import pytest
import ujson

from pathlib import Path
from configparser import ConfigParser
from yarl import URL
from . import ServiceTest

from erasmus.services import BiblesOrg
from erasmus.data import VerseRange

__directory__ = Path(__file__).resolve().parent

passage_sources = {
    'Galatians 3:10-11': (__directory__ / 'biblesorg_Galatians_3:10-11_NASB.txt').read_text(),
    'Mark 5:1': (__directory__ / 'biblesorg_Mark_5:1_NASB.txt').read_text(),
}


def get_json_side_effect(return_value):
    if type(return_value) != str:
        return_value = ujson.dumps(return_value)

    def json_side_effect(*, encoding=None, loads=None, content_type=None):
        return loads(return_value)

    return json_side_effect


class TestBiblesOrg(ServiceTest):
    @pytest.fixture
    def service(self, mock_client_session):
        config = ConfigParser(default_section='erasmus')
        config['services:BiblesOrg'] = {'api_key': 'foo bar baz'}
        return BiblesOrg(config['services:BiblesOrg'], mock_client_session)

    @pytest.fixture
    def mock_search(self, mocker, mock_response):
        return_value = {
            'response': {
                'search': {
                    'result': {
                        'summary': {
                            'total': 50
                        },
                        'verses': [
                            {'reference': 'John 1:1-4'},
                            {'reference': 'Genesis 50:1'}
                        ]
                    }
                }
            }
        }
        mocker.patch.object(mock_response, 'json',
                            new_callable=mocker.AsyncMock,
                            side_effect=get_json_side_effect(return_value))

        return mock_response

    @pytest.fixture(params=[
        {
            'response': {
                'search': {
                    'result': {
                    }
                }
            }
        },
        {
            'response': {
                'search': {
                }
            }
        }
    ])
    def mock_search_failure(self, request, mocker, mock_search):
        mock_search.json.side_effect = get_json_side_effect(request.param)
        return mock_search

    @pytest.fixture
    def search_url(self):
        return URL('https://bibles.org/v2/verses.js').with_query({
            'keyword': 'one two three',
            'precision': 'all',
            'version': 'eng-BIB',
            'sort_order': 'canonical',
            'limit': 20
        })

    @pytest.fixture
    def mock_passage(self, request, mocker, mock_response):
        if hasattr(request, 'param'):
            text = passage_sources[request.param]
        else:
            text = ''

        mocker.patch.object(mock_response, 'json',
                            new_callable=mocker.AsyncMock,
                            side_effect=get_json_side_effect(text))
        mocker.patch.object(mock_response, 'read',
                            new_callable=mocker.AsyncMock,
                            return_value=None)

        return mock_response

    @pytest.fixture(params=[
        {
            'response': {
                'search': {
                    'result': {
                        'passages': []
                    }
                }
            }
        },
        {
            'response': {}
        }
    ])
    def mock_passage_failure(self, request, mocker, mock_passage):
        mock_passage.json.side_effect = get_json_side_effect(request.param)
        return mock_passage

    def get_passages_url(self, version: str, verses: VerseRange) -> str:
        return URL('https://bibles.org/v2/passages.js').with_query({
            'q[]': str(verses),
            'version': version
        })

    def test_init(self, service):
        super().test_init(service)

        assert service._auth.login == 'foo bar baz'
        assert service._auth.password == 'X'
