import pytest
from erasmus.bible_manager import BibleManager
from erasmus.config import ConfigObject
from erasmus.service import Passage
from erasmus.exceptions import ServiceNotSupportedError, BibleNotSupportedError


def MockService(mocker):
    class Service:
        def __init__(self, config):
            self.config = config
            self.get_passage = mocker.AsyncMock()
            self.search = mocker.AsyncMock()

    mock = mocker.Mock(side_effect=Service)

    return mock


class TestBibleManager(object):
    @pytest.fixture(autouse=True)
    def services(self, mocker):
        services = {
            'ServiceOne': MockService(mocker),
            'ServiceTwo': MockService(mocker)
        }

        mocker.patch.dict('erasmus.services.__dict__', services)

        return services

    @pytest.fixture
    def config(self):
        return ConfigObject({
            'services': ConfigObject({
                'ServiceOne': ConfigObject({
                    'api_key': 'service one api key'
                }),
                'ServiceTwo': ConfigObject({
                    'api_key': 'service two api key'
                })
            }),
            'bibles': ConfigObject({
                'bible1': ConfigObject({
                    'name': 'First bible',
                    'service': 'ServiceOne',
                    'service_version': 'eng-bible1'
                }),
                'bible2': ConfigObject({
                    'name': 'Second bible',
                    'service': 'ServiceTwo',
                    'service_version': 'eng-bible2'
                })
            })
        })

    def test_init(self, services, config):
        manager = BibleManager(config)

        assert manager.bible_map['bible1'].name == 'First bible'
        assert type(manager.bible_map['bible1'].service) == services['ServiceOne'].side_effect
        assert manager.bible_map['bible2'].name == 'Second bible'
        assert type(manager.bible_map['bible2'].service) == services['ServiceTwo'].side_effect

    def test_bad_config(self, config):
        config.bibles.bible2['service'] = 'ServiceThree'
        with pytest.raises(ServiceNotSupportedError) as exception:
            BibleManager(config)
            assert exception.service_name == 'ServiceThree'

    def test_get_versions(self, config):
        manager = BibleManager(config)

        result = manager.get_versions()
        assert len(result) == 2
        assert result == [
            ('bible1', 'First bible'), ('bible2', 'Second bible')]

    @pytest.mark.asyncio
    async def test_get_passage(self, config, services):
        manager = BibleManager(config)
        manager.bible_map['bible2'].service.get_passage.return_value = 'blah'

        result = await manager.get_passage('bible2', 'book', 1, 2)
        assert result == 'blah'
        manager.bible_map['bible2'].service.get_passage.assert_called_once_with('eng-bible2', Passage('book', 1, 2))

    @pytest.mark.asyncio
    async def test_get_passage_no_bible(self, config, services):
        manager = BibleManager(config)

        with pytest.raises(BibleNotSupportedError) as exception:
            await manager.get_passage('bible3', 'one', 'two', 'three')
            assert exception.version == 'bible3'

    @pytest.mark.asyncio
    async def test_search(self, config, services):
        manager = BibleManager(config)
        manager.bible_map['bible2'].service.search.return_value = 'blah'

        result = await manager.search('bible2', ['one', 'two', 'three'])
        assert result == 'blah'
        manager.bible_map['bible2'].service.search.assert_called_once_with('eng-bible2', ['one', 'two', 'three'])

    @pytest.mark.asyncio
    async def test_search_no_bible(self, config, services):
        manager = BibleManager(config)

        with pytest.raises(BibleNotSupportedError) as exception:
            await manager.search('bible3', ['one', 'two', 'three'])
            assert exception.version == 'bible3'
