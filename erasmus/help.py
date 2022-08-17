from __future__ import annotations

from typing import TYPE_CHECKING, Any

from discord.ext import commands
from more_itertools import unique_everseen

if TYPE_CHECKING:
    from collections.abc import Mapping


class HelpCommand(commands.DefaultHelpCommand):
    def _get_command_title(self, command: commands.Command[Any, ..., Any], /) -> str:
        return ', '.join(
            f'{self.context.clean_prefix}{s}'
            for s in ([command.name] + list(command.aliases))
        )

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, ..., Any]]],
        /,
    ) -> None:
        bot = self.context.bot

        self.paginator.add_line(bot.description, empty=True)

        filtered = unique_everseen(await self.filter_commands(bot.commands, sort=True))

        self.paginator.add_line('Commands:')
        self.paginator.add_line('---------', empty=True)

        for command in filtered:
            self.paginator.add_line(self._get_command_title(command))
            self.paginator.add_line('    ' + command.short_doc, empty=True)

        self.paginator.add_line(f'{self.context.clean_prefix}<version>')
        self.paginator.add_line(
            '    Look up a verse in a specific version (see '
            f'{self.context.clean_prefix}versions)',
            empty=True,
        )
        self.paginator.add_line(f'{self.context.clean_prefix}s<version>')
        self.paginator.add_line(
            '    Search for terms in a specific version (see '
            f'{self.context.clean_prefix}versions)',
            empty=True,
        )

        self.paginator.add_line()
        self.paginator.add_line(
            f'''You can type the following for more information on a command:

    {self.context.clean_prefix}{self.context.invoked_with} <command>'''
        )

        await self.send_pages()

    def add_command_formatting(
        self,
        command: commands.Command[Any, ..., Any],
        /,
    ) -> None:
        if command.brief:
            self.paginator.add_line(command.brief, empty=True)

        parent = command.full_parent_name
        command_name = command.name if not parent else f'{parent} {command.name}'
        signature = command.signature

        self.paginator.add_line('Usage:')
        self.paginator.add_line('------')

        names = [command_name]
        names.extend(command.aliases)

        for name in names:
            self.paginator.add_line(
                '    ' + self.context.clean_prefix + name + ' ' + signature
            )

        if command.help:
            if command.help[0] != '\n':
                self.paginator.add_line()
            self.paginator.add_line(
                command.help.format(prefix=self.context.clean_prefix)
            )

    async def command_callback(
        self, ctx: commands.Context[Any], /, *, command: str | None = None
    ) -> Any:
        if command and command[0] == ctx.prefix:
            command = command[1:]

        return await super().command_callback(ctx, command=command)
