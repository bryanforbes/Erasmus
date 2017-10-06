from typing import Callable, List, Iterable, Tuple, Set, TypeVar, Iterator  # noqa
from discord.ext import commands
import discord


def pluralizer(word: str, suffix: str = 's') -> Callable[[int], str]:
    def pluralize(value: int) -> str:
        result = f'{value} {word}'

        if value == 0 or value > 1:
            result = f'{result}{suffix}'

        return result

    return pluralize


def _get_command_title(context: commands.Context, name: str, command: commands.Command) -> str:
    return ', '.join(map(
        lambda s: f'{context.prefix}{s}',
        [name] + command.aliases
    ))


def unique_seen(iterable: Iterable[Tuple[str, commands.Command]]) -> Iterator[Tuple[str, commands.Command]]:
    seen = set()  # type: Set[commands.Command]
    for element in iterable:
        if element[1] not in seen:
            seen.add(element[1])
            yield element


class HelpFormatter(commands.HelpFormatter):
    async def filter_command_list(self) -> Iterable[Tuple[str, commands.Command]]:
        iterable = await super().filter_command_list()
        return unique_seen(iterable)

    async def format(self) -> List[discord.Embed]:
        if isinstance(self.command, commands.Command):
            embed = discord.Embed.from_data({
                'title': _get_command_title(self.context, self.command.name, self.command)
            })

            description = []  # type: List[str]

            if self.command.help:
                description.append(self.command.help)

            description.append('**Usage**')
            description.append(f'```{self.get_command_signature()}```')

            embed.description = '\n'.join(description)

            return [embed]

        if isinstance(self.command, commands.Bot):
            filtered = await self.filter_command_list()
            filtered = sorted(filtered)
            embed = discord.Embed.from_data({
                'title': 'Help',
                'description': 'The following commands are available:'
            })
            for name, command in filtered:
                embed.add_field(name=_get_command_title(self.context, name, command),
                                value=command.short_doc or '\u200b',
                                inline=False)

            return [embed]

        return []
