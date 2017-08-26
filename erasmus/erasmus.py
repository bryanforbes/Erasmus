from discord.ext import commands
import re

from .bible_manager import BibleManager
from .exceptions import DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError
from .config import load, ConfigObject

chapterAndVerse_re = re.compile(r'^(?P<chapter>\d+):(?P<verse_start>\d+)(?:-(?P<verse_end>\d+))?$')

class Erasmus(commands.Bot):
    bible_manager: BibleManager
    config: ConfigObject

    def __init__(self, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = load(config_path)
        self.bible_manager = BibleManager(self.config)

        for name, description in self.bible_manager.get_versions():
            command = commands.Command(
                name=name,
                description=description,
                hidden=True,
                pass_context=True,
                callback=self._version_lookup
            )
            self.add_command(command)

        self.add_command(self.versions)

    def run(self):
        return super().run(self.config.api_key)

    async def say(self, content=None, *args, **kwargs):
        if content is not None:
            extensions = ('plain_text',)
            params = { k: kwargs.pop(k, None) for k in extensions }
            plain_text = params.get('plain_text')

            if not plain_text:
                content = f'```{content}```'

        return await super().say(content, *args, **kwargs)

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self):
        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

    @commands.command()
    async def versions(self):
        lines = ['I support the following Bible versions:', '']
        for version, description in self.bible_manager.get_versions():
            version = f'{version}:'.ljust(6)
            lines.append(f'  ~{version} {description}')
        output = '\n'.join(lines)
        await self.say(f'\n{output}\n')

    async def _version_lookup(self, ctx, book: str, chapterAndVerse: str, *args):
        version = ctx.command.name

        if len(args) > 0:
            book = f'{book}{chapterAndVerse}'
            chapterAndVerse = args[0]

        match = chapterAndVerse_re.match(chapterAndVerse)
        if match is not None:
            verse_end = match.group('verse_end')
            if verse_end is None:
                verse_end = -1
            else:
                verse_end = int(verse_end)

            await self.type()

            try:
                passage_text = await self.bible_manager.get_passage(
                    version,
                    book,
                    int(match.group('chapter')),
                    int(match.group('verse_start')),
                    verse_end
                )
            except DoNotUnderstandError:
                await self.say('I do not understand that request')
            except BibleNotSupportedError:
                await self.say(f'~{version} is not supported')
            except ServiceNotSupportedError:
                await self.say(f'The service configured for ~{version} is not supported')
            else:
                await self.say(passage_text)
        else:
            await self.say('I do not understand that request')

__all__ = [ 'Erasmus' ]
