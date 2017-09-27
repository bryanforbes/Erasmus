from .client import Client
from .user import User, ClientUser, Profile
from .game import Game
from .channel import *
from .guild import Guild
from .member import Member, VoiceState
from .message import Message, Attachment
from .permissions import Permissions, PermissionOverwrite
from .role import Role
from .colour import Colour, Color
from . import abc
from .enums import *
from .embeds import Embed
from .shard import AutoShardedClient
from .voice_client import VoiceClient
from collections import namedtuple
from typing import NamedTuple


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int


version_info = ...  # type: VersionInfo
