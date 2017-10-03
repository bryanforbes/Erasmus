from .client import Client, AppInfo
from .user import User, ClientUser, Profile
from .game import Game
from .emoji import Emoji, PartialReactionEmoji
from .channel import *
from .guild import Guild
from .member import Member, VoiceState
from .message import Message, Attachment
from .errors import *
from .calls import CallMessage, GroupCall
from .permissions import Permissions, PermissionOverwrite
from .role import Role
from .file import File
from .colour import Colour, Color
from .invite import Invite
from .object import Object
from . import abc
from .enums import *
from collections import namedtuple
from .embeds import Embed
from .shard import AutoShardedClient
from .webhook import *
from .voice_client import VoiceClient
from .audit_logs import AuditLogChanges, AuditLogEntry, AuditLogDiff
from typing import NamedTuple

__title__: str = ...
__author__: str = ...
__license__: str = ...
__copyright__: str = ...
__version__: str = ...


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int


version_info: VersionInfo = ...
