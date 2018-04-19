from typing import List, Tuple, Optional, Union
from .client import Client
from .activity import Activity, Game, Streaming, Spotify
from .enums import Status


class Shard:
    @property
    def id(self) -> int: ...


class AutoShardedClient(Client):
    @property
    def latency(self) -> float: ...

    @property
    def latencies(self) -> List[Tuple[int, float]]: ...

    async def change_presence(self, *, activity: Optional[Union[Activity, Game, Streaming, Spotify]] = ...,
                              status: Optional[Status] = ...,
                              afk: bool = ..., shard_id: Optional[int] = ...): ...
