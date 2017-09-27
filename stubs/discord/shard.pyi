from typing import List, Tuple, Optional
from .client import Client
from .game import Game
from .enums import Status


class Shard:
    @property
    def id(self) -> int: ...


class AutoShardedClient(Client):
    async def latency(self) -> float: ...

    async def latencies(self) -> List[Tuple[int, float]]: ...

    async def change_presence(self, *, game: Optional[Game] = ..., status: Optional[Status] = ...,
                              afk: bool = ..., shard_id: Optional[int] = ...): ...
