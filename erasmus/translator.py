from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import override

from discord import app_commands

if TYPE_CHECKING:
    import discord

    from .l10n import Localizer


class Translator(app_commands.Translator):
    localizer: Localizer

    def __init__(self, localizer: Localizer, /) -> None:
        self.localizer = localizer

    @override
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContextTypes,
    ) -> str | None:
        message_id: str = ''
        command: object = None

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
            context.location == app_commands.TranslationContextLocation.parameter_name
            or context.location
            == app_commands.TranslationContextLocation.parameter_description
        ):
            suffix = (
                'name'
                if context.location
                == app_commands.TranslationContextLocation.parameter_name
                else 'description'
            )
            message_id = (
                f'{context.data.command.name}.PARAM--{context.data.name}--{suffix}'
            )
            command = context.data.command

        if (
            context.location
            is app_commands.TranslationContextLocation.command_description
            or context.location
            is app_commands.TranslationContextLocation.group_description
        ):
            message_id = f'{message_id}.description'

        if isinstance(command, app_commands.Command | app_commands.Group):
            if command.parent:
                message_id = f'{command.parent.name}__{message_id}'

                if command.parent.parent:
                    message_id = f'{command.parent.parent.name}__{message_id}'

            return self.localizer.format(message_id, locale=locale, use_fallbacks=False)

        return None
