from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import discord
from attrs import define, field
from fluent.runtime import FluentLocalization, FluentResourceLoader

if TYPE_CHECKING:
    from _typeshed import SupportsItems


class Localization(FluentLocalization):
    def format_attribute(
        self,
        message_id: str,
        attribute_id: str,
        args: SupportsItems[str, Any] | None = None,
        /,
    ) -> str:
        for bundle in self._bundles():
            if not bundle.has_message(message_id):
                continue

            message = bundle.get_message(message_id)

            if attribute_id not in message.attributes:
                continue

            value, _ = bundle.format_pattern(message.attributes[attribute_id], args)

            return value

        return attribute_id


@define
class Localizer:
    resource: str
    fallback_locale: discord.Locale
    _loader: FluentResourceLoader = field(init=False)
    _l10n_map: dict[discord.Locale, Localization] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._loader = FluentResourceLoader(
            str(Path(__file__).resolve().parent / '{locale}')
        )
        self._l10n_map = {}

    def format_message(
        self,
        message_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        l10n = self._get_l10n(locale)
        return l10n.format_value(message_id, data)

    def format_attribute(
        self,
        message_id: str,
        attribute_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        l10n = self._get_l10n(locale)
        return l10n.format_attribute(message_id, attribute_id, data)

    def _get_l10n(self, locale: discord.Locale | None, /) -> Localization:
        locale = self.fallback_locale if locale is None else locale

        if locale in self._l10n_map:
            return self._l10n_map[locale]

        locales: list[str] = [str(locale)]

        if locale != self.fallback_locale:
            locales.append(str(self.fallback_locale))

        l10n = Localization(locales, [self.resource], self._loader)
        self._l10n_map[locale] = l10n

        return l10n

    def for_locale(self, locale: discord.Locale, /) -> LocaleLocalizer:
        return LocaleLocalizer(self, locale)

    def for_message(
        self,
        message_id: str,
        /,
        locale: discord.Locale | None = None,
    ) -> MessageLocalizer:
        return MessageLocalizer(
            self.for_locale(self.fallback_locale if locale is None else locale),
            message_id,
        )


@define
class LocaleLocalizer:
    localizer: Localizer
    locale: discord.Locale

    def format_message(
        self,
        message_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        return self.localizer.format_message(message_id, data, self.locale)

    def format_attribute(
        self,
        message_id: str,
        attribute_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        return self.localizer.format_attribute(
            message_id, attribute_id, data, self.locale
        )


@define
class MessageLocalizer:
    localizer: LocaleLocalizer
    message_id: str

    def format_message(self, data: SupportsItems[str, Any] | None = None, /) -> str:
        return self.localizer.format_message(self.message_id, data)

    def format_attribute(
        self,
        attribute_id: str,
        data: SupportsItems[str, Any] | None = None,
        /,
    ) -> str:
        return self.localizer.format_attribute(self.message_id, attribute_id, data)
