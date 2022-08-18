from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, overload

from attrs import define, field
from fluent.runtime import FluentResourceLoader

from .fluent import Localization

if TYPE_CHECKING:
    from _typeshed import SupportsItems

    import discord
    from discord import app_commands


@define
class Localizer:
    default_locale: discord.Locale
    _loader: FluentResourceLoader = field(init=False)
    _l10n_map: dict[discord.Locale, Localization] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._loader = FluentResourceLoader(
            str(Path(__file__).resolve().parent / '{locale}')
        )
        self._l10n_map = {}

    def _create_l10n(self, locale: discord.Locale) -> Localization:
        locales = [str(locale)]

        if locale != self.default_locale:
            locales.append(str(self.default_locale))

        return Localization(locales, ['erasmus.ftl'], self._loader)

    def _get_l10n(
        self,
        locale: discord.Locale | None,
        /,
    ) -> Localization:
        locale = self.default_locale if locale is None else locale

        if locale in self._l10n_map:
            return self._l10n_map[locale]

        l10n = self._l10n_map[locale] = self._create_l10n(locale)

        return l10n

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        locale: discord.Locale | None = None,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: bool,
    ) -> str | None:
        ...

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        locale: discord.Locale | None = None,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: Literal[True] = ...,
    ) -> str:
        ...

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        locale: discord.Locale | None = None,
        data: SupportsItems[str, Any] | None = None,
        use_fallbacks: bool = True,
    ) -> str | None:
        return self._get_l10n(locale).format(
            str(message_id), data, use_fallbacks=use_fallbacks
        )

    def for_locale(self, locale: discord.Locale, /) -> LocaleLocalizer:
        return LocaleLocalizer(self, locale)

    def for_message(
        self,
        message_id: str,
        /,
        locale: discord.Locale | None = None,
    ) -> MessageLocalizer:
        return MessageLocalizer(
            self.for_locale(self.default_locale if locale is None else locale),
            message_id,
        )


@define
class LocaleLocalizer:
    localizer: Localizer
    locale: discord.Locale

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: bool,
    ) -> str | None:
        ...

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: Literal[True] = ...,
    ) -> str:
        ...

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        data: SupportsItems[str, Any] | None = None,
        use_fallbacks: bool = True,
    ) -> str | None:
        return self.localizer.format(
            message_id, data=data, locale=self.locale, use_fallbacks=use_fallbacks
        )


@define
class MessageLocalizer:
    localizer: LocaleLocalizer
    message_id: str

    @overload
    def format(
        self,
        attribute_id: str | None = None,
        /,
        *,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: bool,
    ) -> str | None:
        ...

    @overload
    def format(
        self,
        attribute_id: str | None = None,
        /,
        *,
        data: SupportsItems[str, Any] | None = ...,
        use_fallbacks: Literal[True] = ...,
    ) -> str:
        ...

    def format(
        self,
        attribute_id: str | None = None,
        /,
        *,
        data: SupportsItems[str, Any] | None = None,
        use_fallbacks: bool = True,
    ) -> str | None:
        message_id = self.message_id

        if attribute_id is not None:
            message_id = f'{message_id}.{attribute_id}'

        return self.localizer.format(message_id, data=data, use_fallbacks=use_fallbacks)
