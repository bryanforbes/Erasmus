from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, ClassVar, Literal, get_args

from attrs import define, field, validators
from babel.dates import format_timedelta
from fluent.runtime import AbstractResourceLoader, FluentBundle, FluentLocalization
from fluent.runtime.types import FluentNone, FluentType, merge_options
from pendulum.period import Period

if TYPE_CHECKING:
    from _typeshed import SupportsItems
    from collections.abc import Iterable, Sequence
    from typing_extensions import Self

    from babel import Locale
    from fluent.runtime.resolver import Pattern, TextElement


FormatType = Literal['narrow', 'short', 'long']


@define(slots=False)
class PeriodFormatOptions:
    format: FormatType = field(
        default='long', validator=validators.in_(get_args(FormatType))
    )
    separator: str = field(default=' ')


class FluentPeriod(FluentType, Period):
    default_period_format_options: ClassVar = PeriodFormatOptions()
    options: PeriodFormatOptions

    def _init_options(self, period: Period, **kwargs: object) -> None:
        self.options = merge_options(
            PeriodFormatOptions,  # pyright: ignore
            getattr(
                period, 'options', self.default_period_format_options
            ),  # pyright: ignore
            kwargs,
        )

    @classmethod
    def from_period(cls, period: Period, **kwargs: object) -> Self:
        obj = cls(period.start, period.end)
        obj._init_options(period, **kwargs)
        return obj

    def format(self, locale: Locale | str) -> str:
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
                        format=self.options.format,
                    )
                )

        return self.options.separator.join(parts)


def fluent_period(delta: object, **kwargs: object) -> FluentPeriod:
    if isinstance(delta, FluentPeriod) and not kwargs:
        return delta

    if isinstance(delta, Period):
        return FluentPeriod.from_period(delta, **kwargs)

    raise TypeError(
        "Can't use fluent_period with object {0} for type {1}".format(
            delta, type(delta)
        )
    )


def native_to_fluent(val: object) -> object:
    if isinstance(val, Period):
        return FluentPeriod.from_period(val)

    return val


class Bundle(FluentBundle):
    def format_pattern(
        self,
        pattern: Pattern,
        args: SupportsItems[str, object] | None = ...,
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
        use_isolating: bool = True,
    ) -> None:
        self.fallback_locale = locales[-1] if len(locales) > 1 else None

        super().__init__(
            locales,  # pyright: ignore
            resource_ids,  # pyright: ignore
            resource_loader,
            use_isolating,
            bundle_class=Bundle,
            functions={'PERIOD': fluent_period},
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

            value, _ = bundle.format_pattern(pattern, args)  # pyright: ignore
            return value if isinstance(value, str) else None

        if use_fallbacks:
            if attribute_id:
                return f'{message_id}.{attribute_id}'
            else:
                return message_id

        return None
