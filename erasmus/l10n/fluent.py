from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, ClassVar, Literal, Self, get_args, override

import pendulum
from attrs import define, field, validators
from babel.dates import format_timedelta
from fluent.runtime import AbstractResourceLoader, FluentBundle, FluentLocalization
from fluent.runtime.types import FluentNone, FluentType, merge_options

if TYPE_CHECKING:
    from _typeshed import SupportsItems
    from collections.abc import Iterable, Sequence

    from babel import Locale
    from fluent.runtime.resolver import Pattern, TextElement


FormatType = Literal['narrow', 'short', 'long']


@define(slots=False)
class IntervalFormatOptions:
    format: FormatType = field(
        default='long', validator=validators.in_(get_args(FormatType))
    )
    separator: str = field(default=' ')


class FluentInterval(FluentType, pendulum.Interval):
    default_interval_format_options: ClassVar = IntervalFormatOptions()
    options: IntervalFormatOptions

    def _init_options(self, interval: pendulum.Interval, **kwargs: object) -> None:
        self.options = merge_options(
            IntervalFormatOptions,  # pyright: ignore[reportArgumentType]
            getattr(
                interval, 'options', self.default_interval_format_options
            ),  # pyright: ignore[reportArgumentType]
            kwargs,
        )

    @classmethod
    def from_interval(cls, interval: pendulum.Interval, **kwargs: object) -> Self:
        obj = cls(interval.start, interval.end)
        obj._init_options(interval, **kwargs)
        return obj

    @override
    def format(self, locale: Locale | str) -> str:
        intervals: list[tuple[Literal['hour', 'minute', 'second'], int]] = [
            ('hour', self.hours),
            ('minute', self.minutes),
            ('second', self.remaining_seconds),
        ]

        parts: list[str] = []

        for interval in intervals:
            unit, count = interval

            if abs(count) > 0:
                parts.append(
                    format_timedelta(
                        timedelta(**{f'{unit}s': count}),
                        granularity=unit,
                        threshold=1,
                        locale=locale,
                        format=self.options.format,
                    )
                )

        return self.options.separator.join(parts)


def fluent_interval(delta: object, **kwargs: object) -> FluentInterval:
    if isinstance(delta, FluentInterval) and not kwargs:
        return delta

    if isinstance(delta, pendulum.Interval):
        return FluentInterval.from_interval(delta, **kwargs)

    raise TypeError(
        f"Can't use fluent_interval with object {delta} for type {type(delta)}"
    )


def native_to_fluent(val: object) -> object:
    if isinstance(val, pendulum.Interval):
        return FluentInterval.from_interval(val)

    return val


class Bundle(FluentBundle):
    @override
    def format_pattern(
        self,
        pattern: Pattern,
        args: SupportsItems[str, object] | None = None,
    ) -> tuple[str | FluentNone, list[Exception]]:
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
        *,
        use_isolating: bool = True,
    ) -> None:
        self.fallback_locale = locales[-1] if len(locales) > 1 else None

        super().__init__(
            locales,  # pyright: ignore[reportArgumentType]
            resource_ids,  # pyright: ignore[reportArgumentType]
            resource_loader,
            use_isolating,
            bundle_class=Bundle,
            functions={'INTERVAL': fluent_interval},
        )

    def format(
        self,
        message_id: str,
        args: SupportsItems[str, object] | None = None,
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

            value, _ = bundle.format_pattern(
                pattern, args  # pyright: ignore[reportArgumentType]
            )
            return value if isinstance(value, str) else None

        if use_fallbacks:
            if attribute_id:
                return f'{message_id}.{attribute_id}'

            return message_id

        return None
