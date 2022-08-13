from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any
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

    def format(
        self,
        message_id: str,
        args: SupportsItems[str, Any] | None = None,
        /,
    ) -> str:
        message_id, _, attribute_id = message_id.partition('.')

        if not attribute_id:
            return self.format_value(message_id, args)

        for bundle in self._bundles():
            if not bundle.has_message(message_id):
                continue

            message = bundle.get_message(message_id)

            if attribute_id not in message.attributes:
                continue

            value, _ = bundle.format_pattern(message.attributes[attribute_id], args)

            return value

        return f'{message_id}.{attribute_id}'

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
    fallback_locale: discord.Locale
    _loader: FluentResourceLoader = field(init=False)
    _l10n_map: dict[discord.Locale, Localization] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._loader = FluentResourceLoader(
            str(Path(__file__).resolve().parent / '{locale}')
        )
        self._l10n_map = {}

    def _get_l10n(
        self,
        locale: discord.Locale | None,
        /,
    ) -> Localization:
        locale = self.fallback_locale if locale is None else locale

        if locale in self._l10n_map:
            return self._l10n_map[locale]

        l10n = Localization([str(locale)], ['erasmus.flt'], self._loader)
        self._l10n_map[locale] = l10n

        return l10n

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        data: SupportsItems[str, Any] | None = None,
        locale: discord.Locale | None = None,
    ) -> str:
        return self._get_l10n(locale).format(str(message_id), data)

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

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        return self.localizer.format(str(message_id), data=data, locale=self.locale)


@define
class MessageLocalizer:
    localizer: LocaleLocalizer
    message_id: str

    def format(
        self,
        attribute_id: str | None = None,
        /,
        *,
        data: SupportsItems[str, Any] | None = None,
    ) -> str:
        message_id = self.message_id

        if attribute_id is not None:
            message_id = f'{message_id}.{attribute_id}'

        return self.localizer.format(message_id, data=data)
