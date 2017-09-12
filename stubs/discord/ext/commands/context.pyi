from typing import Any, Optional, List, Dict, Union

from ...abc import Messageable
from .core import Command
from ...guild import Guild
from ...message import Message
from .bot import Bot
from ...channel import TextChannel, DMChannel, GroupChannel
from ...member import Member
from ...user import User, ClientUser
from ...voice_client import VoiceClient


class Context(Messageable):
    message: Message
    bot: Bot
    args: List[Any]
    kwargs: Dict[str, Any]
    prefix: str
    command: Command
    invoked_with: str
    invoked_subcommand: Command
    subcommand_passed: Optional[str]
    command_failed: bool

    async def invoke(self, command: Command, *args, **kwargs) -> Any: ...

    @property
    def valid(self) -> bool: ...

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def channel(self) -> Union[TextChannel, DMChannel, GroupChannel]: ...

    @property
    def author(self) -> Union[Member, User]: ...

    @property
    def me(self) -> Union[Member, ClientUser]: ...

    @property
    def voice_client(self) -> Optional[VoiceClient]: ...
