from typing import Optional


class Game:
    name: str
    url: str
    type: int

    def __init__(self, *, name: Optional[str] = ..., url: Optional[str] = ..., type: int = ...) -> None: ...
