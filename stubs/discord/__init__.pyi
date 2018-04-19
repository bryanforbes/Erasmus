from .client import Client as Client, AppInfo as AppInfo
from .user import User as User, ClientUser as ClientUser, Profile as Profile
from .activity import Activity as Activity, Game as Game, Streaming as Streaming, Spotify as Spotify
from .emoji import Emoji as Emoji, PartialEmoji as PartialEmoji
from .channel import *
from .guild import Guild as Guild
from .member import Member as Member, VoiceState as VoiceState
from .message import Message as Message, Attachment as Attachment
from .errors import *
from .calls import CallMessage as CallMessage, GroupCall as GroupCall
from .permissions import Permissions as Permissions, PermissionOverwrite as PermissionOverwrite
from .role import Role as Role
from .file import File as File
from .colour import Colour as Colour, Color as Color
from .invite import Invite as Invite
from .object import Object as Object
from . import abc as abc
from .enums import *
from collections import namedtuple
from .embeds import Embed as Embed
from .shard import AutoShardedClient as AutoShardedClient
from .webhook import *
from .voice_client import VoiceClient as VoiceClient
from .audit_logs import AuditLogChanges as AuditLogChanges, AuditLogEntry as AuditLogEntry, AuditLogDiff as AuditLogDiff
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
