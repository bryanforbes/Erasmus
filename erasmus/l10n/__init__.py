from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final
from typing_extensions import Self

import discord
from attrs import define, field
from babel.dates import format_timedelta
from discord import app_commands
from fluent.runtime import FluentBundle, FluentLocalization, FluentResourceLoader
from fluent.runtime.errors import FluentFormatError
from fluent.runtime.fallback import AbstractResourceLoader
from fluent.runtime.resolver import Pattern, TextElement
from fluent.runtime.types import FluentType
from pendulum.period import Period

if TYPE_CHECKING:
    from _typeshed import SupportsItems


class FluentPeriod(FluentType, Period):
    def __new__(cls, value: Period, **kwargs: Any) -> Self:
        self: FluentPeriod = super(FluentPeriod, cls).__new__(  # type: ignore
            cls, start=value.start, end=value.end
        )
        return self

    def __init__(self, value: Period, **kwargs: Any) -> None:
        super().__init__(value.start, value.end)

    def format(self, locale: str) -> str:
        periods = [
            ('hour', self.hours),
            ('minute', self.minutes),
            ('second', self.remaining_seconds),
        ]

        parts: list[str] = []

        for period in periods:
            unit, count = period

            if abs(count) > 0:
                parts.append(
                    format_timedelta(
                        timedelta(**{f'{unit}s': count}),
                        granularity=unit,
                        threshold=1,
                        locale=locale,
                    )
                )

        return ' '.join(parts)


def fluent_period(delta: object, **kwargs: Any) -> Any:
    breakpoint()
    if isinstance(delta, FluentPeriod) and not kwargs:
        return delta

    if isinstance(delta, Period):
        return FluentPeriod(delta, **kwargs)

    raise TypeError(
        "Can't use fluent_period with object {0} for type {1}".format(
            delta, type(delta)
        )
    )


def native_to_fluent(val: Any) -> Any:
    if isinstance(val, Period):
        return FluentPeriod(val)

    return val


class Bundle(FluentBundle):
    def format_pattern(
        self, pattern: Pattern | TextElement, args: SupportsItems[str, Any] | None = ...
    ) -> tuple[str, list[FluentFormatError]]:
        if args is not None:
            fluent_args = {
                argname: native_to_fluent(argval) for argname, argval in args.items()
            }
        else:
            fluent_args = {}
        return super().format_pattern(pattern, fluent_args)


class Localization(FluentLocalization):
    def __init__(
        self,
        locales: Sequence[str],
        resource_ids: Iterable[str],
        resource_loader: AbstractResourceLoader,
        use_isolating: bool = ...,
    ) -> None:
        super().__init__(
            locales,
            resource_ids,
            resource_loader,
            use_isolating,
            bundle_class=Bundle,
            functions={'PERIOD': fluent_period},
        )

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
class AppLocalizer:
    fallback_locale: discord.Locale
    _loader: FluentResourceLoader = field(init=False)
    _resource_map: defaultdict[str, dict[discord.Locale, Localization]] = field(
        init=False
    )

    def __attrs_post_init__(self) -> None:
        self._loader = FluentResourceLoader(
            str(Path(__file__).resolve().parent / '{locale}')
        )
        self._resource_map = defaultdict(dict)

    def _get_l10n(
        self,
        resource: str,
        locale: discord.Locale | None,
        /,
    ) -> Localization:
        locale = self.fallback_locale if locale is None else locale
        l10n_map = self._resource_map[resource]

        if locale in l10n_map:
            return l10n_map[locale]

        locales: list[str] = [str(locale)]

        if locale != self.fallback_locale:
            locales.append(str(self.fallback_locale))

        l10n = Localization(locales, [f'{resource}.flt'], self._loader)
        l10n_map[locale] = l10n

        return l10n

    def format_message(
        self,
        resource: str,
        message_id: str | app_commands.locale_str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        return self._get_l10n(resource, locale).format_value(str(message_id), data)

    def format_attribute(
        self,
        resource: str,
        message_id: str | app_commands.locale_str,
        attribute_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        return self._get_l10n(resource, locale).format_attribute(
            str(message_id), attribute_id, data
        )

    def for_resource(self, resource: str, /) -> Localizer:
        return Localizer(self, resource)


@define
class Localizer:
    app_localizer: AppLocalizer
    resource: str

    def format_message(
        self,
        message_id: str | app_commands.locale_str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        return self.app_localizer.format_message(
            self.resource, message_id, data=data, locale=locale
        )

    def format_attribute(
        self,
        message_id: str | app_commands.locale_str,
        attribute_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        return self.app_localizer.format_attribute(
            self.resource, message_id, attribute_id, data=data, locale=locale
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
            self.for_locale(
                self.app_localizer.fallback_locale if locale is None else locale
            ),
            message_id,
        )


@define
class LocaleLocalizer:
    localizer: Localizer
    locale: discord.Locale

    def format_message(
        self,
        message_id: str | app_commands.locale_str,
        /,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        return self.localizer.format_message(str(message_id), data, self.locale)

    def format_attribute(
        self,
        message_id: str | app_commands.locale_str,
        attribute_id: str,
        /,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        return self.localizer.format_attribute(
            str(message_id), attribute_id, data, self.locale
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


APP_LOCALIZER: Final = AppLocalizer(discord.Locale.american_english)


def message_str(
    message_id: str, /, resource: str, **kwargs: Any
) -> app_commands.locale_str:
    return app_commands.locale_str(
        APP_LOCALIZER.format_message(resource, message_id),
        resource=resource,
        message_id=message_id,
        **kwargs,
    )


def attribute_str(
    message_id: str, attribute_id: str, /, resource: str, **kwargs: Any
) -> app_commands.locale_str:
    return app_commands.locale_str(
        APP_LOCALIZER.format_attribute(resource, message_id, attribute_id),
        resource=resource,
        message_id=message_id,
        attribute_id=attribute_id,
        **kwargs,
    )
