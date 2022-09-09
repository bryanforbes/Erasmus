from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import discord
import pytest
import pytest_mock
from discord import app_commands

from erasmus.l10n import LocaleLocalizer, Localizer, MessageLocalizer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class LocalizationMock(Mock):
    format: Mock


class TestLocalizer:
    @pytest.fixture
    def fluent_resource_loader_class(self, mocker: pytest_mock.MockerFixture) -> Mock:
        return mocker.patch('erasmus.l10n.FluentResourceLoader')

    @pytest.fixture
    def fluent_resource_loader(
        self, fluent_resource_loader_class: Mock, mocker: pytest_mock.MockerFixture
    ) -> Mock:
        mock = mocker.Mock()
        fluent_resource_loader_class.return_value = mock
        return mock

    @pytest.fixture
    def en_localization(self, mocker: pytest_mock.MockerFixture) -> LocalizationMock:
        mock = mocker.Mock()
        mock.configure_mock(
            **{'format.return_value': mocker.sentinel.en_localization_format_return}
        )
        return mock

    @pytest.fixture
    def no_localization(self, mocker: pytest_mock.MockerFixture) -> LocalizationMock:
        mock = mocker.Mock()
        mock.configure_mock(
            **{'format.return_value': mocker.sentinel.no_localization_format_return}
        )
        return mock

    @pytest.fixture
    def no_localization_2(self, mocker: pytest_mock.MockerFixture) -> LocalizationMock:
        mock = mocker.Mock()
        mock.configure_mock(
            **{'format.return_value': mocker.sentinel.no_localization_2_format_return}
        )
        return mock

    @pytest.fixture
    def hi_localization(self, mocker: pytest_mock.MockerFixture) -> LocalizationMock:
        mock = mocker.Mock()
        mock.configure_mock(
            **{'format.return_value': mocker.sentinel.hi_localization_format_return}
        )
        return mock

    @pytest.fixture
    def localization_class(
        self,
        mocker: pytest_mock.MockerFixture,
        en_localization: LocalizationMock,
        no_localization: LocalizationMock,
        hi_localization: LocalizationMock,
    ) -> Mock:
        def side_effect(
            locales: Sequence[str], *args: Any, **kwargs: Any
        ) -> LocalizationMock | None:
            if locales[0] == 'nb-NO':
                return no_localization
            elif locales[0] == 'hi-IN':
                return hi_localization
            elif locales[0] == 'en-US':
                return en_localization
            return None

        return mocker.patch('erasmus.l10n.Localization', side_effect=side_effect)

    @pytest.fixture
    def localization_class_side_effect(
        self,
        en_localization: LocalizationMock,
        no_localization_2: LocalizationMock,
        hi_localization: LocalizationMock,
    ) -> Callable[..., Any]:
        def side_effect(
            locales: Sequence[str], *args: Any, **kwargs: Any
        ) -> LocalizationMock | None:
            if locales[0] == 'nb-NO':
                return no_localization_2
            elif locales[0] == 'hi-IN':
                return hi_localization
            elif locales[0] == 'en-US':
                return en_localization
            return None

        return side_effect

    @pytest.fixture
    def localizer_format(self, mocker: pytest_mock.MockerFixture) -> Mock:
        return mocker.patch('erasmus.l10n.Localizer.format')

    def test_init(
        self, fluent_resource_loader_class: Mock, fluent_resource_loader: Mock
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)

        fluent_resource_loader_class.assert_called_once_with(
            str(
                Path(__file__).resolve().parent.parent / 'erasmus' / 'l10n' / '{locale}'
            )
        )
        assert localizer.default_locale == discord.Locale.american_english
        assert localizer._loader is fluent_resource_loader

    def test_format(
        self,
        localization_class: Mock,
        en_localization: LocalizationMock,
        fluent_resource_loader: Mock,
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        localizer.format('generic-error')

        localization_class.assert_called_once_with(
            ['en-US'], ['erasmus.ftl'], fluent_resource_loader
        )
        en_localization.format.assert_called_once_with(
            'generic-error', None, use_fallbacks=True
        )

    def test_format_locale(
        self,
        mocker: pytest_mock.MockerFixture,
        localization_class: Mock,
        en_localization: LocalizationMock,
        no_localization: LocalizationMock,
        hi_localization: LocalizationMock,
        fluent_resource_loader: Mock,
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        assert (
            localizer.format('generic-error', locale=discord.Locale.norwegian)
            == mocker.sentinel.no_localization_format_return
        )
        assert (
            localizer.format(app_commands.locale_str('generic-error'))
            == mocker.sentinel.en_localization_format_return
        )
        assert (
            localizer.format(
                'no-private-message',
                data={},
                use_fallbacks=False,
                locale=discord.Locale.hindi,
            )
            == mocker.sentinel.hi_localization_format_return
        )

        localization_class.assert_has_calls(
            [  # type: ignore
                mocker.call(
                    ['nb-NO', 'en-US'],
                    ['erasmus.ftl'],
                    fluent_resource_loader,
                ),
                mocker.call(
                    ['en-US'],
                    ['erasmus.ftl'],
                    fluent_resource_loader,
                ),
                mocker.call(
                    ['hi-IN', 'en-US'],
                    ['erasmus.ftl'],
                    fluent_resource_loader,
                ),
            ]
        )
        no_localization.format.assert_has_calls(
            [
                mocker.call('generic-error', None, use_fallbacks=True),  # type: ignore
            ]
        )
        en_localization.format.assert_has_calls(
            [
                mocker.call('generic-error', None, use_fallbacks=True),  # type: ignore
            ]
        )
        hi_localization.format.assert_has_calls(
            [
                mocker.call(
                    'no-private-message', {}, use_fallbacks=False
                ),  # type: ignore
            ]
        )

    def test_begin_reload(
        self,
        mocker: pytest_mock.MockerFixture,
        localization_class: Mock,
        localization_class_side_effect: Callable[..., Any],
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        localizer.format('generic-error', locale=discord.Locale.norwegian)

        localization_class.side_effect = localization_class_side_effect
        with localizer.begin_reload():
            pass

        assert (
            localizer.format('generic-error', locale=discord.Locale.norwegian)
            == mocker.sentinel.no_localization_2_format_return
        )

    def test_begin_reload_raises(
        self,
        mocker: pytest_mock.MockerFixture,
        localization_class: Mock,
        localization_class_side_effect: Callable[..., Any],
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        localizer.format('generic-error', locale=discord.Locale.norwegian)

        localization_class.side_effect = localization_class_side_effect
        with suppress(Exception), localizer.begin_reload():
            localizer.format('generic-error', locale=discord.Locale.norwegian)
            assert (
                localizer.format('generic-error', locale=discord.Locale.norwegian)
                == mocker.sentinel.no_localization_2_format_return
            )
            raise TypeError

        assert (
            localizer.format('generic-error', locale=discord.Locale.norwegian)
            == mocker.sentinel.no_localization_format_return
        )

    def test_for_locale(
        self, mocker: pytest_mock.MockerFixture, localizer_format: Mock
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        locale_localizer = localizer.for_locale(discord.Locale.norwegian)

        assert isinstance(locale_localizer, LocaleLocalizer)
        assert locale_localizer.localizer is localizer
        assert locale_localizer.locale == discord.Locale.norwegian

        locale_localizer.format('generic-error')
        locale_localizer.format('no-private-message', data={}, use_fallbacks=False)
        localizer_format.assert_has_calls(
            [  # type: ignore
                mocker.call(
                    'generic-error',
                    data=None,
                    locale=discord.Locale.norwegian,
                    use_fallbacks=True,
                ),
                mocker.call(
                    'no-private-message',
                    data={},
                    locale=discord.Locale.norwegian,
                    use_fallbacks=False,
                ),
            ]
        )

    def test_for_message(
        self, mocker: pytest_mock.MockerFixture, localizer_format: Mock
    ) -> None:
        localizer = Localizer(discord.Locale.american_english)
        en_message_localizer = localizer.for_message('serverprefs')
        no_message_localizer = localizer.for_message(
            'serverprefs__setdefault', locale=discord.Locale.norwegian
        )

        assert isinstance(en_message_localizer, MessageLocalizer)
        assert isinstance(en_message_localizer.localizer, LocaleLocalizer)
        assert en_message_localizer.message_id == 'serverprefs'
        assert isinstance(no_message_localizer, MessageLocalizer)
        assert isinstance(no_message_localizer.localizer, LocaleLocalizer)
        assert no_message_localizer.message_id == 'serverprefs__setdefault'

        en_message_localizer.format()
        en_message_localizer.format(data={}, use_fallbacks=False)
        en_message_localizer.format('description')
        en_message_localizer.format('description', data={}, use_fallbacks=False)
        no_message_localizer.format()
        no_message_localizer.format(data={}, use_fallbacks=False)
        no_message_localizer.format('description')
        no_message_localizer.format('description', data={}, use_fallbacks=False)

        localizer_format.assert_has_calls(
            [  # type: ignore
                mocker.call(
                    'serverprefs',
                    data=None,
                    locale=discord.Locale.american_english,
                    use_fallbacks=True,
                ),
                mocker.call(
                    'serverprefs',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs.description',
                    data=None,
                    locale=discord.Locale.american_english,
                    use_fallbacks=True,
                ),
                mocker.call(
                    'serverprefs.description',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs__setdefault',
                    data=None,
                    locale=discord.Locale.norwegian,
                    use_fallbacks=True,
                ),
                mocker.call(
                    'serverprefs__setdefault',
                    data={},
                    locale=discord.Locale.norwegian,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs__setdefault.description',
                    data=None,
                    locale=discord.Locale.norwegian,
                    use_fallbacks=True,
                ),
                mocker.call(
                    'serverprefs__setdefault.description',
                    data={},
                    locale=discord.Locale.norwegian,
                    use_fallbacks=False,
                ),
            ]
        )
