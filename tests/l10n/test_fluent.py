from __future__ import annotations

from pathlib import Path
from typing import Any

import pendulum
import pytest
from fluent.runtime.fallback import FluentResourceLoader

from erasmus.l10n.fluent import Localization


class TestLocalization:
    @pytest.fixture
    def loader(self) -> FluentResourceLoader:
        return FluentResourceLoader(
            str(Path(__file__).resolve().parent / 'data' / '{locale}')
        )

    @pytest.mark.parametrize(
        'locales,expected_fallback_locale',
        [
            (['en-US'], None),
            (['nb-NO', 'en-US'], 'en-US'),
        ],
    )
    def test_fallback_locale(
        self,
        locales: list[str],
        loader: FluentResourceLoader,
        expected_fallback_locale: str | None,
    ) -> None:
        l10n = Localization(locales, ['test.ftl'], loader)
        assert l10n.fallback_locale == expected_fallback_locale

    @pytest.mark.parametrize(
        'locales,args,kwargs,expected',
        [
            (['en-US'], ('message',), {}, 'This is a message'),
            (
                ['en-US'],
                ('message.attribute',),
                {},
                'This is an attribute',
            ),
            (
                ['en-US'],
                ('message', {'something': 'Something'}),
                {},
                'This is a message',
            ),
            (
                ['en-US'],
                ('message.attribute', {'something': 'Something'}),
                {},
                'This is an attribute',
            ),
            (
                ['en-US'],
                ('missing-message',),
                {},
                'missing-message',
            ),
            (
                ['en-US'],
                ('message.missing-attribute',),
                {},
                'message.missing-attribute',
            ),
            (
                ['en-US'],
                ('another-message',),
                {},
                'This is another message with \u2068something\u2069',
            ),
            (
                ['en-US'],
                ('another-message', {'something': 'a variable'}),
                {},
                'This is another message with \u2068a variable\u2069',
            ),
            (
                ['en-US'],
                ('message.another-attribute',),
                {},
                'This is another attribute with \u2068something\u2069',
            ),
            (
                ['en-US'],
                ('message.another-attribute', {'something': 'a variable'}),
                {},
                'This is another attribute with \u2068a variable\u2069',
            ),
            (
                ['hi-IN', 'en-US'],
                ('message',),
                {},
                'This is a message in Hindi',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message',),
                {},
                'This is a message in Norwegian',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.attribute',),
                {},
                'This is an attribute in Norwegian',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message', {'something': 'Something'}),
                {},
                'This is a message in Norwegian',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.attribute', {'something': 'Something'}),
                {},
                'This is an attribute in Norwegian',
            ),
            (
                ['nb-NO', 'en-US'],
                ('missing-message',),
                {},
                'missing-message',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.missing-attribute',),
                {},
                'message.missing-attribute',
            ),
            (
                ['nb-NO', 'en-US'],
                ('another-message',),
                {},
                'This is another message with \u2068something\u2069',
            ),
            (
                ['nb-NO', 'en-US'],
                ('another-message', {'something': 'a variable'}),
                {},
                'This is another message with \u2068a variable\u2069',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.another-attribute',),
                {},
                'This is another attribute with \u2068something\u2069',
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.another-attribute', {'something': 'a variable'}),
                {},
                'This is another attribute with \u2068a variable\u2069',
            ),
            (
                ['en-US'],
                ('missing-message',),
                {'use_fallbacks': False},
                None,
            ),
            (
                ['en-US'],
                ('message.missing-attribute',),
                {'use_fallbacks': False},
                None,
            ),
            (
                ['nb-NO', 'en-US'],
                ('missing-message',),
                {'use_fallbacks': False},
                None,
            ),
            (
                ['nb-NO', 'en-US'],
                ('message.missing-attribute',),
                {'use_fallbacks': False},
                None,
            ),
            (
                ['nb-NO', 'en-US'],
                ('another-message',),
                {'use_fallbacks': False},
                None,
            ),
        ],
    )
    def test_format(
        self,
        locales: list[str],
        loader: FluentResourceLoader,
        args: tuple[str, dict[str, Any] | None],
        kwargs: dict[str, Any],
        expected: str | None,
    ) -> None:
        l10n = Localization(locales, ['test.ftl'], loader)
        assert l10n.format(*args, **kwargs) == expected

    @pytest.mark.parametrize(
        'locales,message_id,seconds,expected',
        [
            (
                ['en-US'],
                'period-message',
                9010,
                'There are \u20682 hours 30 minutes 9 seconds\u2069 left',
            ),
            (
                ['en-US'],
                'period-message',
                90,
                'There are \u20681 minute 29 seconds\u2069 left',
            ),
            (
                ['hi-IN', 'en-US'],
                'period-message',
                9010,
                'There are \u20682 घंटे 30 मिनट 9 सेकंड\u2069 left in Hindi',
            ),
            (
                ['nb-NO', 'en-US'],
                'period-message',
                9010,
                'There are \u20682 timer 30 minutter 9 sekunder\u2069 left '
                'in Norwegian',
            ),
            (
                ['nb-NO', 'en-US'],
                'period-message',
                90,
                'There are \u20681 minutt 29 sekunder\u2069 left in Norwegian',
            ),
            (
                ['en-US'],
                'period-message-implicit',
                90,
                'There are \u20681 minute 29 seconds\u2069 left',
            ),
            (
                ['en-US'],
                'period-message-format-short',
                90,
                'There are \u20681 min 29 sec\u2069 left',
            ),
            (
                ['nb-NO', 'en-US'],
                'period-message-format-short',
                90,
                'There are \u20681 min 29 sek\u2069 left in Norwegian',
            ),
            (
                ['en-US'],
                'period-message-format-narrow',
                90,
                'There are \u20681m 29s\u2069 left',
            ),
            (
                ['nb-NO', 'en-US'],
                'period-message-format-narrow',
                90,
                'There are \u20681m 29s\u2069 left in Norwegian',
            ),
            (
                ['en-US'],
                'period-message-separator',
                90,
                'There are \u20681 minute, 29 seconds\u2069 left',
            ),
        ],
    )
    def test_format_period(
        self,
        loader: FluentResourceLoader,
        locales: list[str],
        message_id: str,
        seconds: int,
        expected: str,
    ) -> None:
        l10n = Localization(locales, ['test.ftl'], loader)
        period = pendulum.now().add(seconds=seconds).diff()
        assert l10n.format(message_id, {'period': period}) == expected

    def test_format_period_invalid(self, loader: FluentResourceLoader) -> None:
        l10n = Localization(['en-US'], ['test.ftl'], loader)

        assert (
            l10n.format('period-message', {'period': 1})
            == 'There are \u2068PERIOD()\u2069 left'
        )
