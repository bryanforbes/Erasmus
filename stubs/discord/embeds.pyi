from datetime import datetime
from typing import Union, Dict, Any, List
from .colour import Colour


class _EmptyEmbed:
    ...


EmptyEmbed = ...  # type: _EmptyEmbed


class EmbedProxy:
    def __init__(self, layer: Dict[str, Any]) -> None: ...

    def __len__(self) -> int: ...

    def __getattr__(self, attr: str) -> _EmptyEmbed: ...


class Embed:
    title: str
    type: str
    description: str
    url: str
    timestamp: Union[datetime, _EmptyEmbed]

    Empty = EmptyEmbed

    def __init__(self, *, color: Union[Colour, int] = None,
                 colour: Union[Colour, int] = None,
                 title: str = None, url: str = None, description: str = None,
                 timestamp: datetime = None) -> None: ...

    @property
    def colour(self) -> Union[Colour, _EmptyEmbed]: ...

    @colour.setter
    def colour(self, value: Union[Colour, _EmptyEmbed, int]) -> None: ...

    color = colour

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> 'Embed': ...

    @property
    def footer(self) -> EmbedProxy: ...

    def set_footer(self, *, text: Union[str, _EmptyEmbed] = EmptyEmbed,
                   icon_url: Union[str, _EmptyEmbed] = EmptyEmbed) -> 'Embed': ...

    @property
    def image(self) -> EmbedProxy: ...

    def set_image(self, *, url: str) -> 'Embed': ...

    @property
    def thumbnail(self) -> EmbedProxy: ...

    def set_thumbnail(self, *, url: str) -> 'Embed': ...

    @property
    def video(self) -> EmbedProxy: ...

    @property
    def provider(self) -> EmbedProxy: ...

    @property
    def author(self) -> EmbedProxy: ...

    def set_author(self, *, name: str, url: Union[str, _EmptyEmbed] = EmptyEmbed,
                   icon_url: Union[str, _EmptyEmbed] = EmptyEmbed) -> 'Embed': ...

    @property
    def fields(self) -> List[EmbedProxy]: ...

    def add_field(self, *, name: str, value: str, inline: bool = True) -> 'Embed': ...

    def clear_fields(self) -> None: ...

    def remove_field(self, index: int) -> None: ...

    def set_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> 'Embed': ...

    def to_dict(self) -> Dict[str, Any]: ...
