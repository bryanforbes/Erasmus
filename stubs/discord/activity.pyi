from typing import Tuple, Any, List, Optional, Dict, Union
from mypy_extensions import TypedDict
from .enums import ActivityType
from .colour import Colour
from datetime import datetime, timedelta

__all__ = ('Activity', 'Streaming', 'Game', 'Spotify')


class _ActivityTag(object):
    __slots__: Tuple[Any]


class Timestamps(TypedDict, total=False):
    start: int
    end: int


class Assets(TypedDict, total=False):
    large_image: str
    large_text: str
    small_image: str
    small_text: str


class Party(TypedDict, total=False):
    id: str
    size: List[int]


class Activity(_ActivityTag):
    application_id: str
    name: str
    url: str
    type: ActivityType
    state: str
    details: str
    timestamps: Timestamps
    assets: Assets
    party: Party

    def __init__(self, *, state: str = ..., details: str = ..., timestamps: Timestamps = ...,
                 assets: Assets = ..., party: Party = ..., application_id: str = ..., name: str = ...,
                 url: str = ..., flags: int = ..., sync_id: str = ..., session_id: str = ...,
                 type: ActivityType = ...) -> None: ...

    @property
    def start(self) -> Optional[datetime]: ...

    @property
    def end(self) -> Optional[datetime]: ...

    @property
    def large_image_url(self) -> Optional[str]: ...

    @property
    def small_image_url(self) -> Optional[str]: ...

    @property
    def large_image_text(self) -> Optional[str]: ...

    @property
    def small_image_text(self) -> Optional[str]: ...


class Game(_ActivityTag):
    name: str

    def __init__(self, name: str, *, start: datetime = ..., end: datetime = ...) -> None: ...

    @property
    def type(self) -> ActivityType: ...

    @property
    def start(self) -> Optional[datetime]: ...

    @property
    def end(self) -> Optional[datetime]: ...


class Streaming(_ActivityTag):
    name: str
    url: str
    details: Optional[str]
    assets: Assets

    def __init__(self, *, name: str, url: str, details: Optional[str] = ..., assets: Assets = ...) -> None: ...

    @property
    def type(self) -> ActivityType: ...

    @property
    def twitch_name(self) -> Optional[str]: ...


class Spotify:
    @property
    def type(self) -> ActivityType: ...

    @property
    def colour(self) -> Colour: ...

    @property
    def color(self) -> Colour: ...

    @property
    def name(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def artists(self) -> List[str]: ...

    @property
    def artist(self) -> str: ...

    @property
    def album(self) -> str: ...

    @property
    def album_cover_url(self) -> str: ...

    @property
    def track_id(self) -> str: ...

    @property
    def start(self) -> datetime: ...

    @property
    def end(self) -> datetime: ...

    @property
    def duration(self) -> timedelta: ...

    @property
    def party_id(self) -> str: ...


def create_activity(data: Dict[str, Any]) -> Union[Activity, Game, Streaming, Spotify]: ...
