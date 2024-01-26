from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict, Unpack, overload

from attrs import define, field, frozen
from discord import app_commands
from discord.ext import commands
from fluent.runtime import FluentResourceLoader

from .fluent import Localization

if TYPE_CHECKING:
    from _typeshed import SupportsItems
    from collections.abc import Iterator

    import discord


# These need to be mapped because pontoon uses the full code rather than the two-letter
# code that Discord uses
_fluent_locale_map = {
    'no': 'nb-NO',
    'hi': 'hi-IN',
}


def _get_fluent_locale(locale: discord.Locale) -> str:
    result = str(locale)
    if result in _fluent_locale_map:
        return _fluent_locale_map[result]

    return str(locale)


class FormatKwargs(TypedDict):
    data: NotRequired[SupportsItems[str, object] | None]


class FormatFallbackKwargs(FormatKwargs):
    use_fallbacks: bool


class FormatFallbackTrueKwargs(FormatKwargs):
    use_fallbacks: NotRequired[Literal[True]]


class FormatAnyKwargs(FormatKwargs):
    use_fallbacks: NotRequired[bool]


class LocalizerFormatKwargs(FormatKwargs):
    locale: NotRequired[discord.Locale | None]


class LocalizerFormatFallbackKwargs(LocalizerFormatKwargs, FormatFallbackKwargs): ...


class LocalizerFormatFallbackTrueKwargs(
    LocalizerFormatKwargs, FormatFallbackTrueKwargs
): ...


class LocalizerFormatAnyKwargs(LocalizerFormatKwargs):
    use_fallbacks: NotRequired[bool]


def _get_group_prefix(
    group_prefix: str | app_commands.Group | commands.GroupCog, /
) -> str:
    if isinstance(group_prefix, app_commands.Group):
        group_prefix = str(group_prefix.__discord_app_commands_group_name__)
    elif isinstance(group_prefix, commands.GroupCog):
        group_prefix = str(group_prefix.__cog_group_name__)

    return group_prefix


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
        locales = [_get_fluent_locale(locale)]

        if locale != self.default_locale:
            locales.append(_get_fluent_locale(self.default_locale))

        return Localization(locales, ['erasmus.ftl'], self._loader)

    def _get_l10n(self, locale: discord.Locale | None, /) -> Localization:
        locale = self.default_locale if locale is None else locale

        if locale in self._l10n_map:
            return self._l10n_map[locale]

        self._l10n_map[locale] = self._create_l10n(locale)

        return self._l10n_map[locale]

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[LocalizerFormatFallbackKwargs],
    ) -> str | None: ...

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[LocalizerFormatFallbackTrueKwargs],
    ) -> str: ...

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        *,
        locale: discord.Locale | None = None,
        data: SupportsItems[str, object] | None = None,
        use_fallbacks: bool = True,
    ) -> str | None:
        return self._get_l10n(locale).format(
            str(message_id), data, use_fallbacks=use_fallbacks
        )

    @contextmanager
    def begin_reload(self) -> Iterator[None]:
        old_map = self._l10n_map
        try:
            self._l10n_map = {}
            yield
        except Exception:
            self._l10n_map = old_map
            raise

    def for_group(
        self, group_prefix: str | app_commands.Group | commands.GroupCog, /
    ) -> GroupLocalizer:
        return GroupLocalizer(self, _get_group_prefix(group_prefix))

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


@frozen
class GroupLocalizer:
    localizer: Localizer
    group_prefix: str

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[LocalizerFormatFallbackKwargs],
    ) -> str | None: ...

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[LocalizerFormatFallbackTrueKwargs],
    ) -> str: ...

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[LocalizerFormatAnyKwargs],
    ) -> str | None:
        return self.localizer.format(f'{self.group_prefix}__{message_id}', **kwargs)

    def for_group(
        self, group_prefix: str | app_commands.Group | commands.GroupCog, /
    ) -> GroupLocalizer:
        group_prefix = _get_group_prefix(group_prefix)

        return self.localizer.for_group(f'{self.group_prefix}__{group_prefix}')

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
                self.localizer.default_locale if locale is None else locale
            ),
            message_id,
        )


@frozen
class LocaleLocalizer:
    localizer: Localizer | GroupLocalizer
    locale: discord.Locale

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[FormatFallbackKwargs],
    ) -> str | None: ...

    @overload
    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[FormatFallbackTrueKwargs],
    ) -> str: ...

    def format(
        self,
        message_id: str | app_commands.locale_str,
        /,
        **kwargs: Unpack[FormatAnyKwargs],
    ) -> str | None:
        return self.localizer.format(message_id, locale=self.locale, **kwargs)


@frozen
class MessageLocalizer:
    localizer: LocaleLocalizer | GroupLocalizer
    message_id: str

    @overload
    def format(
        self,
        attribute_id: str | None = None,
        /,
        **kwargs: Unpack[FormatFallbackKwargs],
    ) -> str | None: ...

    @overload
    def format(
        self,
        attribute_id: str | None = None,
        /,
        **kwargs: Unpack[FormatFallbackTrueKwargs],
    ) -> str: ...

    def format(
        self,
        attribute_id: str | None = None,
        /,
        **kwargs: Unpack[FormatAnyKwargs],
    ) -> str | None:
        message_id = self.message_id

        if attribute_id is not None:
            message_id = f'{message_id}.{attribute_id}'

        return self.localizer.format(message_id, **kwargs)
