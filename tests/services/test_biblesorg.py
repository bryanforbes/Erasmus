import pytest
from erasmus.services import BiblesOrg
from erasmus.service import Passage
from erasmus.exceptions import DoNotUnderstandError

@pytest.fixture
def good_mock_response(mocker, mock_response):
    mocker.patch.object(mock_response, 'json', new_callable=mocker.AsyncMock, return_value={
        'response': {
            'search': {
                'result': {
                    'passages': [
                        { 'text': '<h3>Title</h3><sup class="v">1</sup>This  is the\ntext' }
                    ]
                }
            }
        }
    })

    return mock_response

@pytest.fixture
def bad_mock_response(mocker, mock_response):
    mocker.patch.object(mock_response, 'json', new_callable=mocker.AsyncMock, return_value={
        'response': {
            'search': {
                'result': {
                    'passages': []
                }
            }
        }
    })

    return mock_response

def test_init():
    class Config:
        api_key = 'foo bar baz'

    config = Config()
    service = BiblesOrg(config)
    assert service.config is config
    assert service._auth.login == 'foo bar baz'
    assert service._auth.password == 'X'

@pytest.mark.parametrize('args,expected', [
    (['esv', Passage('John', 1, 2, 3)], 'John+1:2-3&version=esv'),
    (['nasb', Passage('Mark', 5, 20)], 'Mark+5:20&version=nasb')
])
@pytest.mark.asyncio
async def test_get_passage(args, expected, mocker, good_mock_response, mock_client_session):
    class Config:
        api_key = 'foo bar baz'

    config = Config()
    service = BiblesOrg(config)

    response = await service.get_passage(*args)
    assert mock_client_session.get.call_args == mocker.call(f'https://bibles.org/v2/passages.js?q[]={expected}')
    assert response == '1. This is the text'

@pytest.mark.asyncio
async def test_get_passage_no_passages(bad_mock_response):
    class Config:
        api_key = 'foo bar baz'

    config = Config()
    service = BiblesOrg(config)

    with pytest.raises(DoNotUnderstandError):
        await service.get_passage('esv', Passage('John', 1, 2, 3))
