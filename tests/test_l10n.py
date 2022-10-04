from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import discord
import pytest
import pytest_mock
from discord import app_commands
from discord.ext import commands

from erasmus.l10n import GroupLocalizer, LocaleLocalizer, Localizer, MessageLocalizer

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
                    locale=discord.Locale.norwegian,
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
                    locale=discord.Locale.american_english,
                ),
                mocker.call(
                    'serverprefs',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs.description',
                    locale=discord.Locale.american_english,
                ),
                mocker.call(
                    'serverprefs.description',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs__setdefault',
                    locale=discord.Locale.norwegian,
                ),
                mocker.call(
                    'serverprefs__setdefault',
                    data={},
                    locale=discord.Locale.norwegian,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'serverprefs__setdefault.description',
                    locale=discord.Locale.norwegian,
                ),
                mocker.call(
                    'serverprefs__setdefault.description',
                    data={},
                    locale=discord.Locale.norwegian,
                    use_fallbacks=False,
                ),
            ]
        )

    def test_for_group(
        self, mocker: pytest_mock.MockerFixture, localizer_format: Mock
    ) -> None:
        app_group_mock: Mock = mocker.Mock(
            spec=app_commands.Group, __discord_app_commands_group_name__='app-group'
        )
        group_cog_mock: Mock = mocker.Mock(
            spec=commands.GroupCog, __cog_group_name__='group-cog'
        )
        localizer = Localizer(discord.Locale.american_english)

        group_localizer = localizer.for_group('foo')
        sub_group_localizer = group_localizer.for_group('bar')
        app_group_localizer = localizer.for_group(app_group_mock)
        group_cog_localizer = localizer.for_group(group_cog_mock)

        group_locale_localizer = group_localizer.for_locale(discord.Locale.swedish)
        group_en_message_localizer = sub_group_localizer.for_message('baz')
        group_de_message_localizer = sub_group_localizer.for_message(
            'spam', locale=discord.Locale.german
        )

        assert isinstance(group_localizer, GroupLocalizer)
        assert isinstance(sub_group_localizer, GroupLocalizer)
        assert isinstance(app_group_localizer, GroupLocalizer)
        assert isinstance(group_cog_localizer, GroupLocalizer)
        assert isinstance(group_locale_localizer, LocaleLocalizer)
        assert isinstance(group_en_message_localizer, MessageLocalizer)
        assert isinstance(group_de_message_localizer, MessageLocalizer)

        assert group_localizer.localizer is localizer
        assert sub_group_localizer.localizer is localizer
        assert app_group_localizer.localizer is localizer
        assert group_cog_localizer.localizer is localizer

        group_localizer.format('generic-error', locale=discord.Locale.norwegian)
        group_localizer.format('no-private-message', data={}, use_fallbacks=False)
        sub_group_localizer.format('generic-error', locale=discord.Locale.norwegian)
        sub_group_localizer.format('no-private-message', data={}, use_fallbacks=False)
        app_group_localizer.format('generic-error', locale=discord.Locale.norwegian)
        app_group_localizer.format('no-private-message', data={}, use_fallbacks=False)
        group_cog_localizer.format('generic-error', locale=discord.Locale.norwegian)
        group_cog_localizer.format('no-private-message', data={}, use_fallbacks=False)

        group_locale_localizer.format('generic-error')
        group_locale_localizer.format(
            'no-private-message', data={}, use_fallbacks=False
        )
        group_en_message_localizer.format()
        group_en_message_localizer.format(data={}, use_fallbacks=False)
        group_en_message_localizer.format('description')
        group_en_message_localizer.format('description', data={}, use_fallbacks=False)
        group_de_message_localizer.format()
        group_de_message_localizer.format(data={}, use_fallbacks=False)
        group_de_message_localizer.format('description')
        group_de_message_localizer.format('description', data={}, use_fallbacks=False)

        localizer_format.assert_has_calls(
            [  # type: ignore
                mocker.call('foo__generic-error', locale=discord.Locale.norwegian),
                mocker.call('foo__no-private-message', data={}, use_fallbacks=False),
                mocker.call('foo__bar__generic-error', locale=discord.Locale.norwegian),
                mocker.call(
                    'foo__bar__no-private-message', data={}, use_fallbacks=False
                ),
                mocker.call(
                    'app-group__generic-error', locale=discord.Locale.norwegian
                ),
                mocker.call(
                    'app-group__no-private-message', data={}, use_fallbacks=False
                ),
                mocker.call(
                    'group-cog__generic-error', locale=discord.Locale.norwegian
                ),
                mocker.call(
                    'group-cog__no-private-message', data={}, use_fallbacks=False
                ),
                mocker.call(
                    'foo__generic-error',
                    locale=discord.Locale.swedish,
                ),
                mocker.call(
                    'foo__no-private-message',
                    data={},
                    locale=discord.Locale.swedish,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'foo__bar__baz',
                    locale=discord.Locale.american_english,
                ),
                mocker.call(
                    'foo__bar__baz',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'foo__bar__baz.description',
                    locale=discord.Locale.american_english,
                ),
                mocker.call(
                    'foo__bar__baz.description',
                    data={},
                    locale=discord.Locale.american_english,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'foo__bar__spam',
                    locale=discord.Locale.german,
                ),
                mocker.call(
                    'foo__bar__spam',
                    data={},
                    locale=discord.Locale.german,
                    use_fallbacks=False,
                ),
                mocker.call(
                    'foo__bar__spam.description',
                    locale=discord.Locale.german,
                ),
                mocker.call(
                    'foo__bar__spam.description',
                    data={},
                    locale=discord.Locale.german,
                    use_fallbacks=False,
                ),
            ]
        )
