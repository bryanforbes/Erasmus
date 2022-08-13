from __future__ import annotations

from typing import Any

import discord
from discord import app_commands

from .l10n import Localizer


class Translator(app_commands.Translator):
    localizer: Localizer

    def __init__(self, localizer: Localizer, /) -> None:
        self.localizer = localizer

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        message_id: str = ''
        translation: str | None = None
        command: Any | None = None

        if (
            context.location == app_commands.TranslationContextLocation.command_name
            or context.location
            == app_commands.TranslationContextLocation.command_description
            or context.location == app_commands.TranslationContextLocation.group_name
            or context.location
            == app_commands.TranslationContextLocation.group_description
        ):
            command = context.data
            message_id = command.name
        elif (
            context.location is app_commands.TranslationContextLocation.parameter_name
            or context.location
            is app_commands.TranslationContextLocation.parameter_description
        ):
            message_id = f'{context.data.command.name}--PARAMS--{context.data.name}'
            command = context.data.command

        if (
            context.location
            is app_commands.TranslationContextLocation.command_description
            or context.location
            is app_commands.TranslationContextLocation.group_description
            or context.location
            is app_commands.TranslationContextLocation.parameter_description
        ):
            message_id = f'{message_id}.description'

        if isinstance(command, app_commands.Command):
            if command.parent:
                message_id = f'{command.parent.name}__{message_id}'

                if command.parent.parent:
                    message_id = f'{command.parent.parent.name}__{message_id}'

            translation = self.localizer.format(message_id, locale=locale)

            if translation == message_id:
                translation = None

        return translation
