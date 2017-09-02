import asyncio


class BaseConnector(object):
    def __init__(self, *, keepalive_timeout: int,
                 force_close: bool, limit: int,
                 limit_per_host: int, enable_cleanup_closed: bool,
                 loop: asyncio.AbstractEventLoop) -> None: ...

    def __del__(self) -> None: ...

    @property
    def loop(self) -> asyncio.AbstractEventLoop: ...
