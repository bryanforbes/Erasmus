from discord.ext import commands
from discord.message import Message
import re

from .data import Passage
from .bible_manager import BibleManager
from .exceptions import DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError
from .json import JSONObject, load

number_re = re.compile(r'^\d+$')


class Context(commands.Context):
    async def send(self, content: str = None, *, plain_text: bool = None, **kwargs) -> Message:
        if content is not None:
            if not plain_text:
                content = f'```{content}```'

        return await super().send(content, **kwargs)


class Erasmus(commands.Bot):
    bible_manager: BibleManager
    config: JSONObject

    def __init__(self, config_path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        with open(config_path, 'r') as f:
            self.config = load(f)

        self.bible_manager = BibleManager(self.config)

        for name, description in self.bible_manager.get_versions():
            lookup_command = commands.Command(
                name=name,
                description=f'Lookup a verse in {description}',
                hidden=True,
                pass_context=True,
                callback=self._version_lookup
            )
            search_command = commands.Command(
                name=f's{name}',
                description=f'Search in {description}',
                hidden=True,
                pass_context=True,
                callback=self._version_search
            )
            self.add_command(lookup_command)
            self.add_command(search_command)

        self.add_command(self.versions)

    def run(self, *args, **kwargs) -> None:
        super().run(self.config.api_key)

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: Message) -> None:
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_ready(self) -> None:
        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

    @commands.command()
    async def versions(self, ctx: Context) -> None:
        lines = ['I support the following Bible versions:', '']
        for version, description in self.bible_manager.get_versions():
            version = f'{version}:'.ljust(6)
            lines.append(f'  ~{version} {description}')

        lines.append("\nYou can search any version by prefixing the version command with 's' (ex. ~sesv [terms...])")

        output = '\n'.join(lines)
        await ctx.send(f'\n{output}\n')

    async def _version_lookup(self, ctx: Context, book: str, chapter_and_verse: str, *args) -> None:
        version = ctx.command.name

        if len(args) > 0 and number_re.match(book) is not None:
            book = f'{book} {chapter_and_verse}'
            chapter_and_verse = args[0]

        passage = Passage.from_string(f'{book} {chapter_and_verse}')

        if passage is not None:
            async with ctx.typing():
                try:
                    passage_text = await self.bible_manager.get_passage(
                        version,
                        passage
                    )
                except DoNotUnderstandError:
                    await ctx.send('I do not understand that request')
                except BibleNotSupportedError:
                    await ctx.send(f'~{version} is not supported')
                except ServiceNotSupportedError:
                    await ctx.send(f'The service configured for ~{version} is not supported')
                else:
                    await ctx.send(passage_text)
        else:
            await ctx.send('I do not understand that request')

    async def _version_search(self, ctx: Context, *terms) -> None:
        version = ctx.command.name[1:]

        async with ctx.typing():
            try:
                results = await self.bible_manager.search(version, list(terms))
            except BibleNotSupportedError:
                await ctx.send(f'~{ctx.command.name} is not supported')
            else:
                verses = ', '.join([str(verse) for verse in results.verses])
                matches = 'match'

                if results.total == 0 or results.total > 1:
                    matches = 'matches'

                if results.total <= 20:
                    await ctx.send(f'I have found {results.total} {matches} to your search:\n{verses}')
                else:
                    await ctx.send(f'I have found {results.total} {matches} to your search. '
                                   f'Here are the first 20 {matches}:\n{verses}')


__all__ = ['Erasmus']
