from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, overload
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
    fallback_locale: str | None

    def __init__(
        self,
        locales: Sequence[str],
        resource_ids: Iterable[str],
        resource_loader: AbstractResourceLoader,
        use_isolating: bool = ...,
    ) -> None:
        self.fallback_locale = locales[-1] if len(locales) > 1 else None
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
        *,
        use_fallbacks: bool = True,
    ) -> str | None:
        message_id, _, attribute_id = message_id.partition('.')

        for bundle in self._bundles():
            if (
                not use_fallbacks
                and self.fallback_locale is not None
                and bundle.locales[0] == self.fallback_locale
            ):
                return None

            if not bundle.has_message(message_id):
                continue

            message = bundle.get_message(message_id)
            pattern: TextElement | Pattern

            if attribute_id:
                if attribute_id not in message.attributes:
                    continue

                pattern = message.attributes[attribute_id]
            else:
                if not message.value:
                    continue

                pattern = message.value

            value, _ = bundle.format_pattern(pattern, args)
            return value

        if use_fallbacks:
            return f'{message_id}.{attribute_id}'

        return None


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

        return Localization(locales, ['erasmus.flt'], self._loader)

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
