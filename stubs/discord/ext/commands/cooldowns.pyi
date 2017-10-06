from typing import Optional
import enum

from .context import Context


class BucketType(enum.Enum):
    default = 0
    user = 0
    guild = 2
    channel = 2


class Cooldown:
    rate: int
    per: float
    type: BucketType

    def __init__(self, rate: int, per: float, type: BucketType) -> None: ...

    def get_tokens(self, current: Optional[int] = ...) -> int: ...

    def update_rate_limit(self) -> Optional[float]: ...

    def reset(self) -> None: ...

    def copy(self): 'Cooldown'


class CooldownMapping:
    def __init__(self, original: Cooldown) -> None: ...

    @property
    def valid(self) -> bool: ...

    def get_bucket(self, ctx: Context) -> Cooldown: ...
