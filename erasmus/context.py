import discord
from discord.ext import commands
from .data import Passage

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

    async def send_error_to_author(self, text: str = None, *, embed: discord.Embed = None) -> discord.Message:
        if embed is not None:
            embed = discord.Embed.from_data(embed.to_dict())
        else:
            embed = discord.Embed()

        embed.color = discord.Color.red()

        return await self.send_to_author(text, embed=embed)

    async def send_to_author(self, text: str = None, *, embed: discord.Embed = None) -> discord.Message:
        if text is not None:
            if embed is None:
                embed = discord.Embed()
            embed.description = text

        mention = None  # type: str

        if not isinstance(self.message.channel, discord.DMChannel) and \
                not isinstance(self.message.channel, discord.GroupChannel):
            mention = self.author.mention

        return await self.send(mention, embed=embed)
