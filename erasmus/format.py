from typing import Callable, List, Iterable, Tuple, Set, TypeVar, Iterator  # noqa
from discord.ext import commands


def pluralizer(word: str, suffix: str = 's') -> Callable[[int], str]:
    def pluralize(value: int) -> str:
        result = f'{value} {word}'

        if value == 0 or value > 1:
            result = f'{result}{suffix}'

        return result

    return pluralize


def unique_seen(iterable: Iterable[Tuple[str, commands.Command]]) -> Iterator[Tuple[str, commands.Command]]:
    seen = set()  # type: Set[commands.Command]
    for element in iterable:
        if element[1] not in seen:
            seen.add(element[1])
            yield element


class HelpFormatter(commands.HelpFormatter):
    def _get_command_title(self, name: str, command: commands.Command) -> str:
        return ', '.join(map(
            lambda s: f'{self.clean_prefix}{s}',
            [name] + command.aliases
        ))

    async def filter_command_list(self) -> Iterable[Tuple[str, commands.Command]]:
        iterable = await super().filter_command_list()
        return unique_seen(iterable)

    async def format(self) -> List[str]:
        self._paginator = commands.Paginator()
        add_line = self._paginator.add_line

        if isinstance(self.command, commands.Command):
            if self.command.brief:
                add_line(self.command.brief, empty=True)

            signature_parts = self.get_command_signature().split(' ')

            if '|' in signature_parts[0]:
                names = signature_parts[0][2:-1].split('|')
            else:
                names = [signature_parts[0][1:]]

            add_line('Usage:')
            add_line('------')

            for name in names:
                add_line('    ' + signature_parts[0][0] + name + ' ' + ' '.join(signature_parts[1:]))

            if self.command.help:
                if self.command.help[0] != '\n':
                    add_line()
                add_line(self.command.help.format(prefix=self.clean_prefix))

            self._paginator.close_page()
            return self._paginator.pages

        if isinstance(self.command, commands.Bot):
            filtered = await self.filter_command_list()
            filtered = sorted(filtered)

            add_line('Commands:')
            add_line('---------', empty=True)

            for name, command in filtered:
                add_line(self._get_command_title(name, command))
                add_line('    ' + command.short_doc, empty=True)

            add_line(f'{self.clean_prefix}<version>')
            add_line(f'    Look up a verse in a specific version (see {self.clean_prefix}versions)', empty=True)
            add_line(f'{self.clean_prefix}s<version>')
            add_line(f'    Search for terms in a specific version (see {self.clean_prefix}versions)', empty=True)

        add_line()
        add_line(f'''You can type the following for more information on a command:

    {self.clean_prefix}{self.context.invoked_with} <command>''')

        return self._paginator.pages
