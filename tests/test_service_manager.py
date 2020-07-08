import pytest

from erasmus.data import Passage, VerseRange
from erasmus.service_manager import ServiceManager


def MockService(mocker):
    class Service:
        def __init__(self, *, config, session):
            self.config = config
            self.session = session
            self.get_passage = mocker.CoroutineMock()
            self.search = mocker.CoroutineMock()

    mock = mocker.Mock(side_effect=Service)

    return mock


class TestServiceManager(object):
    @pytest.fixture(autouse=True)
    def services(self, mocker):
        services = {
            '__all__': ['ServiceOne', 'ServiceTwo'],
            'ServiceOne': MockService(mocker),
            'ServiceTwo': MockService(mocker),
        }

        mocker.patch.dict('erasmus.services.__dict__', services, clear=True)

        return services

    @pytest.fixture
    def config(self):
        return {'services': {'ServiceTwo': {'api_key': 'foo bar baz'}}}

    @pytest.fixture
    def bible1(self, MockBible):
        return MockBible(
            command='bible1',
            name='Bible 1',
            abbr='BIB1',
            service='ServiceOne',
            service_version='service-BIB1',
        )

    @pytest.fixture
    def bible2(self, MockBible):
        return MockBible(
            command='bible2',
            name='Bible 2',
            abbr='BIB2',
            service='ServiceTwo',
            service_version='service-BIB2',
        )

    def test_init(self, services, config, mock_client_session):
        manager = ServiceManager.from_config(config, mock_client_session)

        assert manager.service_map['ServiceOne'].config is None
        assert (
            type(manager.service_map['ServiceOne'])
            == services['ServiceOne'].side_effect
        )
        assert (
            manager.service_map['ServiceTwo'].config is config['services']['ServiceTwo']
        )
        assert (
            type(manager.service_map['ServiceTwo'])
            == services['ServiceTwo'].side_effect
        )

    def test_container_methods(self, config, mock_client_session):
        manager = ServiceManager.from_config(config, mock_client_session)

        assert 'ServiceOne' in manager
        assert 'ServiceTwo' in manager
        assert '__all__' not in manager
        assert len(manager) == 2

    @pytest.mark.asyncio
    async def test_get_passage(self, config, bible2, mock_client_session):
        manager = ServiceManager.from_config(config, mock_client_session)
        manager.service_map['ServiceTwo'].get_passage.return_value = Passage(
            'blah', VerseRange.from_string('Genesis 1:2')
        )

        result = await manager.get_passage(
            bible2, VerseRange.from_string('Genesis 1:2')
        )

        assert result == Passage('blah', VerseRange.from_string('Genesis 1:2'), 'BIB2')
        manager.service_map['ServiceTwo'].get_passage.assert_called_once_with(
            bible2, VerseRange.from_string('Genesis 1:2')
        )

    @pytest.mark.asyncio
    async def test_search(self, config, bible1, mock_client_session):
        manager = ServiceManager.from_config(config, mock_client_session)
        manager.service_map['ServiceOne'].search.return_value = 'blah'

        result = await manager.search(
            bible1, ['one', 'two', 'three'], limit=10, offset=20
        )
        assert result == 'blah'
        manager.service_map['ServiceOne'].search.assert_called_once_with(
            bible1, ['one', 'two', 'three'], limit=10, offset=20
        )
