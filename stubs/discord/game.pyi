from typing import Optional, Iterable, Iterator, Union


class Game(Iterable[Union[str, int]]):
    name: str
    url: str
    type: int

    def __init__(self, *, name: Optional[str] = ..., url: Optional[str] = ..., type: int = ...) -> None: ...

    def __iter__(self) -> Iterator[Union[str, int]]: ...
