from typing import cast

import discord
import re

from discord.ext import commands
from .data import VerseRange
from .bible_manager import BibleManager
from .exceptions import (
    DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError,
    BookNotUnderstoodError, ReferenceNotUnderstoodError
)
from .json import JSONObject, load
from .format import pluralizer
from .context import Context

number_re = re.compile(r'^\d+$')
pluralize_match = pluralizer('match', 'es')


class Erasmus(commands.Bot):
    bible_manager: BibleManager
    config: JSONObject

    def __init__(self, config_path, *args, **kwargs) -> None:
        with open(config_path, 'r') as f:
            self.config = load(f)

        kwargs['command_prefix'] = self.config.command_prefix

        super().__init__(*args, **kwargs)

        self.bible_manager = BibleManager(self.config)

        for name, description in self.bible_manager.get_versions():
            self.command(name=name,
                         description=f'Look up a verse in {description}',
                         hidden=True)(self._version_lookup)
            self.command(name=f's{name}',
                         description=f'Search in {description}',
                         hidden=True)(self._version_search)

        self.add_command(self.versions)

    def run(self, *args, **kwargs) -> None:
        super().run(self.config.api_key)

    async def get_context(self, message: discord.Message, *, cls=Context) -> Context:
        return cast(Context, await super().get_context(message, cls=cls))

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message) -> None:
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_ready(self) -> None:
        await self.change_presence(game=discord.Game(name=f'| {self.command_prefix}versions'))

        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

    async def on_command_error(self, ctx: Context, exc: Exception) -> None:
        message = 'An error occurred'
        if isinstance(exc, commands.CommandInvokeError):
            if isinstance(exc.original, BookNotUnderstoodError):
                message = f'I do not understand the book "{exc.original.book}"'
            elif isinstance(exc.original, DoNotUnderstandError):
                message = 'I do not understand that request'
            elif isinstance(exc.original, ReferenceNotUnderstoodError):
                message = f'I do not understand the reference {exc.original.reference}'
            elif isinstance(exc.original, BibleNotSupportedError):
                message = f'{self.command_prefix}{exc.original.version} is not supported'
            elif isinstance(exc.original, ServiceNotSupportedError):
                message = f'The service configured for {self.command_prefix}{ctx.invoked_with} is not supported'
            else:
                print(exc)
                message = 'An error occurred'
        elif isinstance(exc, commands.NoPrivateMessage):
            message = 'This command is not available in private messages'
        elif isinstance(exc, commands.MissingRequiredArgument):
            message = f'The required argument `{exc.param}` is missing'
        else:
            print(exc)

        await ctx.send_error_to_author(message)

    @commands.command()
    async def versions(self, ctx: Context) -> None:
        lines = ['I support the following Bible versions:', '']
        lines += [f'  `{self.command_prefix}{version}`: {description}'
                  for version, description in self.bible_manager.get_versions()]

        lines.append("\nYou can search any version by prefixing the version command with 's' "
                     f"(ex. `{self.command_prefix}sesv terms...`)")

        output = '\n'.join(lines)
        await ctx.send_to_author(f'\n{output}\n')

    async def _version_lookup(self, ctx: Context, *, reference: str) -> None:
        version = ctx.invoked_with

        verses = VerseRange.from_string(reference)
        if verses is not None:
            async with ctx.typing():
                passage = await self.bible_manager.get_passage(version, verses)
                await ctx.send_passage(passage)
        else:
            await ctx.send_error_to_author('I do not understand that request')

    async def _version_search(self, ctx: Context, *terms) -> None:
        version = ctx.invoked_with[1:]

        async with ctx.typing():
            results = await self.bible_manager.search(version, list(terms))
            matches = pluralize_match(results.total)
            output = f'I have found {matches} to your search'

            if results.total > 0:
                verses = '\n'.join([f'- {verse}' for verse in results.verses])
                if results.total <= 20:
                    output = f'{output}:\n\n{verses}'
                else:
                    limit = pluralize_match(20)
                    output = f'{output}. Here are the first {limit}:\n\n{verses}'

            await ctx.send_to_author(output)


__all__ = ['Erasmus']
