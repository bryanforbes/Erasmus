from __future__ import annotations

from typing import Any, Optional, List, Mapping
from discord.ext import commands
from more_itertools import unique_everseen

from .context import Context


class HelpCommand(commands.DefaultHelpCommand[Context]):
    def _get_command_title(self, command: commands.Command[Context]) -> str:
        return ', '.join(
            map(
                lambda s: f'{self.clean_prefix}{s}',
                [command.name] + list(command.aliases),
            )
        )

    async def send_bot_help(
        self,
        mapping: Mapping[
            Optional[commands.Cog[Context]], List[commands.Command[Context]]
        ],
    ) -> None:
        assert self.context is not None
        bot = self.context.bot

        self.paginator.add_line(bot.description, empty=True)

        filtered = unique_everseen(await self.filter_commands(bot.commands, sort=True))

        self.paginator.add_line('Commands:')
        self.paginator.add_line('---------', empty=True)

        for command in filtered:
            self.paginator.add_line(self._get_command_title(command))
            self.paginator.add_line('    ' + command.short_doc, empty=True)

        self.paginator.add_line(f'{self.clean_prefix}<version>')
        self.paginator.add_line(
            '    Look up a verse in a specific version (see '
            f'{self.clean_prefix}versions)',
            empty=True,
        )
        self.paginator.add_line(f'{self.clean_prefix}s<version>')
        self.paginator.add_line(
            '    Search for terms in a specific version (see '
            f'{self.clean_prefix}versions)',
            empty=True,
        )

        self.paginator.add_line()
        self.paginator.add_line(
            f'''You can type the following for more information on a command:

    {self.clean_prefix}{self.context.invoked_with} <command>'''
        )

        await self.send_pages()

    def add_command_formatting(self, command: commands.Command[Context]) -> None:
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
            self.paginator.add_line('    ' + self.clean_prefix + name + ' ' + signature)

        if command.help:
            if command.help[0] != '\n':
                self.paginator.add_line()
            self.paginator.add_line(command.help.format(prefix=self.clean_prefix))

    async def command_callback(
        self, ctx: Context, *, command: Optional[str] = None
    ) -> Any:
        if command:
            if command[0] == ctx.prefix:
                command = command[1:]

        return await super().command_callback(ctx, command=command)
