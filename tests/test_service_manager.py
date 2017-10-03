import pytest
from configparser import ConfigParser
from erasmus.service_manager import ServiceManager, Bible
from erasmus.data import VerseRange, Passage


def MockService(mocker):
    class Service:
        def __init__(self, config):
            self.config = config
            self.get_passage = mocker.AsyncMock()
            self.search = mocker.AsyncMock()

    mock = mocker.Mock(side_effect=Service)

    return mock


class TestServiceManager(object):
    @pytest.fixture(autouse=True)
    def services(self, mocker):
        services = {
            '__all__': ['ServiceOne', 'ServiceTwo'],
            'ServiceOne': MockService(mocker),
            'ServiceTwo': MockService(mocker)
        }

        mocker.patch.dict('erasmus.services.__dict__', services, clear=True)

        return services

    @pytest.fixture
    def config(self):
        config = ConfigParser(default_section='erasmus')
        config['services:ServiceTwo'] = {'api_key': 'foo bar baz'}
        return config

    def test_init(self, services, config):
        manager = ServiceManager(config)

        assert manager.service_map['ServiceOne'].config is None
        assert type(manager.service_map['ServiceOne']) == services['ServiceOne'].side_effect
        assert manager.service_map['ServiceTwo'].config is config['services:ServiceTwo']
        assert type(manager.service_map['ServiceTwo']) == services['ServiceTwo'].side_effect

    def test_container_methods(self, config):
        manager = ServiceManager(config)

        assert 'ServiceOne' in manager
        assert 'ServiceTwo' in manager
        assert '__all__' not in manager
        assert len(manager) == 2

    @pytest.mark.asyncio
    async def test_get_passage(self, config):
        manager = ServiceManager(config)
        manager.service_map['ServiceTwo'].get_passage.return_value = \
            Passage('blah', VerseRange.from_string('Genesis 1:2'))

        bible = Bible('bible2', 'Bible 2', 'BIB2', 'ServiceTwo', 'service-BIB2')
        result = await manager.get_passage(bible, VerseRange.from_string('Genesis 1:2'))

        assert result == Passage('blah', VerseRange.from_string('Genesis 1:2'), 'BIB2')
        manager.service_map['ServiceTwo'].get_passage.assert_called_once_with(
            'service-BIB2',
            VerseRange.from_string('Genesis 1:2'))

    @pytest.mark.asyncio
    async def test_search(self, config):
        manager = ServiceManager(config)
        manager.service_map['ServiceOne'].search.return_value = 'blah'

        bible = Bible('bible1', 'Bible 1', 'BIB1', 'ServiceOne', 'service-BIB1')
        result = await manager.search(bible, ['one', 'two', 'three'])
        assert result == 'blah'
        manager.service_map['ServiceOne'].search.assert_called_once_with('service-BIB1', ['one', 'two', 'three'])
