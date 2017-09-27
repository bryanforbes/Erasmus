from typing import Optional, ContextManager, AsyncContextManager
from asyncio import AbstractEventLoop


class timeout(ContextManager['timeout'], AsyncContextManager['timeout']):
    def __init__(self, timeout: Optional[int], *,
                 loop: Optional[AbstractEventLoop] = ...) -> None: ...

    @property
    def expired(self) -> bool: ...
