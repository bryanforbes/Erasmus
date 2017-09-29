from typing import cast

import discord
import re

from discord.ext import commands
from .data import VerseRange, Passage
from .bible_manager import BibleManager
from .exceptions import DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError, BookNotUnderstoodError
from .json import JSONObject, load
from .format import pluralizer

number_re = re.compile(r'^\d+$')

truncation_warning = '**The passage was too long and has been truncated:**\n\n'
max_length = 2048 - (len(truncation_warning) + 1)


class Context(commands.Context):
    async def send_passage(self, passage: Passage) -> discord.Message:
        text = passage.text

        if len(text) > 2048:
            text = f'{truncation_warning}{text[:max_length]}\u2026'

        embed = discord.Embed.from_data({
            'description': text,
            'footer': {
                'text': passage.citation
            }
        })

        return await self.send_to_author(embed=embed)

    async def send_to_author(self, text: str = None, *, embed: discord.Embed = None) -> discord.Message:
        if text is not None:
            if embed is None:
                embed = discord.Embed()
            embed.description = text

        return await self.send(self.author.mention, embed=embed)


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
        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

        await self.change_presence(game=discord.Game(name=f'| {self.command_prefix}versions'))

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

        try:
            verses = VerseRange.from_string(reference)
        except BookNotUnderstoodError as err:
            await ctx.send_to_author(f'I do not understand the book "{err.book}"')
        else:
            if verses is not None:
                async with ctx.typing():
                    try:
                        passage = await self.bible_manager.get_passage(version, verses)
                    except DoNotUnderstandError:
                        await ctx.send_to_author('I do not understand that request')
                    except BibleNotSupportedError as err:
                        await ctx.send_to_author(f'{self.command_prefix}{err.version} is not supported')
                    except ServiceNotSupportedError:
                        await ctx.send_to_author(f'The service configured for {self.command_prefix}{version} '
                                                 'is not supported')
                    else:
                        await ctx.send_passage(passage)
            else:
                await ctx.send_to_author('I do not understand that request')

    async def _version_search(self, ctx: Context, *terms) -> None:
        version = ctx.invoked_with[1:]

        async with ctx.typing():
            try:
                results = await self.bible_manager.search(version, list(terms))
            except BibleNotSupportedError:
                await ctx.send_to_author(f'`{self.command_prefix}{ctx.invoked_with}` is not supported')
            else:
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
