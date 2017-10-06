import pytest
from urllib.parse import urlencode
from configparser import ConfigParser
import json
from . import ServiceTest

from erasmus.services import BiblesOrg
from erasmus.data import VerseRange

passage_text = {
    'Galatians 3:10-11': ('<p class=\"p\"><sup id=\"Gal.3.10\" class=\"v\">10</sup>'
                          'For as many as are of the works of the Law are under a '
                          'curse; for it is written, “C<span class=\"sc\">URSED IS '
                          'EVERYONE WHO DOES NOT ABIDE BY ALL THINGS WRITTEN IN THE '
                          'BOOK OF THE LAW</span>, <span class=\"sc\">TO '
                          'PERFORM THEM</span>.”<sup id=\"Gal.3.11\" class=\"v\">11'
                          '</sup>Now that no one is justified by the Law before God '
                          'is evident; for, “T<span class=\"sc\">HE RIGHTEOUS MAN '
                          'SHALL LIVE BY FAITH</span>.”</p>'),
    'Mark 5:1': '<h3 class=\"s\">The Gerasene Demoniac</h3>\n<p class=\"p\"><sup id=\"Mark.5.1\" class=\"v\">1</sup>They came to the other side of the sea, into the country of the Gerasenes.</p>' # noqa
}


def get_json_side_effect(return_value):
    def json_side_effect(*, encoding=None, loads=None, content_type=None):
        return loads(json.dumps(return_value))
    return json_side_effect


class TestBiblesOrg(ServiceTest):
    @pytest.fixture
    def service(self):
        config = ConfigParser(default_section='erasmus')
        config['services:BiblesOrg'] = {'api_key': 'foo bar baz'}
        return BiblesOrg(config['services:BiblesOrg'])

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
        return 'https://bibles.org/v2/verses.js?' + urlencode({
            'keyword': 'one two three',
            'precision': 'all',
            'version': 'esv',
            'sort_order': 'canonical',
            'limit': 20
        })

    @pytest.fixture
    def mock_passage(self, request, mocker, mock_response):
        if hasattr(request, 'param'):
            text = passage_text[request.param]
        else:
            text = ''

        return_value = {
            'response': {
                'search': {
                    'result': {
                        'passages': [
                            {'text': text}
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
        return f'https://bibles.org/v2/passages.js?' + urlencode({
            'q[]': str(verses),
            'version': version
        })

    def test_init(self, service):
        super().test_init(service)

        assert service._auth.login == 'foo bar baz'
        assert service._auth.password == 'X'
