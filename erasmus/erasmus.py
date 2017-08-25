from discord.ext import commands
import re

from .bible_manager import BibleManager
from .exceptions import DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError
from .config import load

query_re = re.compile(r'^~(?P<version>\w+) (?P<book>\w+) (?P<chapter>\d+):(?P<verse_min>\d+)(?:-(?P<verse_max>\d+))?')

class Erasmus(commands.Bot):
    def __init__(self, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = load(config_path)
        self.bible_manager = BibleManager(self.config)

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

    async def process_commands(self, message):
        _internal_channel = message.channel
        _internal_author = message.author

        match = query_re.match(message.content)
        if match is not None:
            verse_max = match.group('verse_max')
            if verse_max is None:
                verse_max = -1
            else:
                verse_max = int(verse_max)

            await self.type()

            version = match.group('version')
            try:
                verse = await self.bible_manager.get_passage(
                    version,
                    match.group('book'),
                    int(match.group('chapter')),
                    int(match.group('verse_min')),
                    verse_max
                )
            except DoNotUnderstandError:
                await self.say('I do not understand that request')
            except BibleNotSupportedError:
                await self.say(f'~{version} is not supported')
            except ServiceNotSupportedError:
                await self.say(f'The service configured for ~{version} is not supported')
            else:
                await self.say(verse)
        else:
            await super().process_commands(message)

    async def on_ready(self):
        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

    @commands.command()
    async def versions(self):
        lines = ['I support the following Bible versions:']
        for version, description in self.bible_manager.get_versions():
            lines.append(f'  ~{version}: {description}')
        output = '\n'.join(lines)
        await self.say(f'\n{output}\n')

__all__ = [ 'Erasmus' ]
