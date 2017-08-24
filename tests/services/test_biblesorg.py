import pytest
from erasmus.services import BiblesOrg

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

@pytest.mark.asyncio
async def test_get_verse(good_mock_response):
    class Config:
        api_key = 'foo bar baz'

    config = Config()
    service = BiblesOrg(config)

    response = await service.get_verse('esv', 'John', 1, 2, 3)
    assert response == '1. This is the text'
