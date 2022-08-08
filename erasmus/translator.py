from __future__ import annotations

import discord
from discord import app_commands

from .l10n import AppLocalizer


class Translator(app_commands.Translator):
    app_localizer: AppLocalizer

    def __init__(self, app_localizer: AppLocalizer, /) -> None:
        self.app_localizer = app_localizer

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        resource: str = string.extras['resource']
        message_id: str = string.extras['message_id']

        match context:
            case (
                app_commands.TranslationContext.command_name
                | app_commands.TranslationContext.parameter_name
            ):
                return self.app_localizer.format_message(
                    resource, message_id, locale=locale
                )
            case (
                app_commands.TranslationContext.command_description
                | app_commands.TranslationContext.parameter_description
            ):
                return self.app_localizer.format_attribute(
                    resource, message_id, 'description', locale=locale
                )
            case _:
                pass

        return str(string)
