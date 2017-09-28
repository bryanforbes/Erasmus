from .mixins import Hashable
from datetime import datetime


class Object(Hashable):
    def __init__(self, id: str) -> None: ...

    @property
    def created_at(self) -> datetime: ...
