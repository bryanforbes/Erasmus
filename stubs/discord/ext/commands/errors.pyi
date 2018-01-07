from typing import Optional, List
from discord.errors import DiscordException
from inspect import Parameter
from .cooldowns import Cooldown
import discord

__all__ = ['CommandError', 'MissingRequiredArgument', 'BadArgument',
           'NoPrivateMessage', 'CheckFailure', 'CommandNotFound',
           'DisabledCommand', 'CommandInvokeError', 'TooManyArguments',
           'UserInputError', 'CommandOnCooldown', 'NotOwner',
           'MissingPermissions', 'BotMissingPermissions']


class CommandError(DiscordException):
    def __init__(self, message: Optional[str] = ..., *args) -> None: ...


class UserInputError(CommandError):
    ...


class CommandNotFound(CommandError):
    ...


class MissingRequiredArgument(UserInputError):
    param: Parameter

    def __init__(self, param: Parameter) -> None: ...


class TooManyArguments(UserInputError):
    ...


class BadArgument(UserInputError):
    ...


class CheckFailure(CommandError):
    ...


class NoPrivateMessage(CheckFailure):
    ...


class NotOwner(CheckFailure):
    ...


class DisabledCommand(CommandError):
    ...


class CommandInvokeError(CommandError):
    original: Exception

    def __init__(self, e: Exception) -> None: ...


class CommandOnCooldown(CommandError):
    cooldown: Cooldown
    retry_after: float

    def __init__(self, cooldown: Cooldown, retry_after: float) -> None: ...


class MissingPermissions(CheckFailure):
    missing_perms: List[discord.Permissions]

    def __init__(self, missing_perms: List[discord.Permissions], *args) -> None: ...


class BotMissingPermissions(CheckFailure):
    missing_perms: List[discord.Permissions]

    def __init__(self, missing_perms: List[discord.Permissions], *args) -> None: ...
