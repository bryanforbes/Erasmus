import asyncio
from typing import Dict, Mapping, Iterable, Callable, Union, AsyncContextManager, Any
from .connector import BaseConnector
from .abc import AbstractCookieJar
from .helpers import BasicAuth
from .client_reqrep import ClientResponse


class ClientSession(AsyncContextManager['ClientSession']):
    def __init__(self, *, connector: BaseConnector,
                 loop: asyncio.AbstractEventLoop,
                 cookies: Dict[str, str],
                 headers: Mapping[str, str],
                 skip_auto_headers: Iterable[str],
                 auth: BasicAuth,
                 version: str,
                 cookie_jar: AbstractCookieJar,
                 json_serialize: Callable[..., str],
                 raise_for_status: bool,
                 read_timeout: float,
                 conn_timeout: Union[None, float]) -> None: ...

    def get(self, url: str, *, allow_redirects: bool = ..., **kwargs) -> AsyncContextManager[ClientResponse]: ...

    def post(self, url: str, *, data: Dict[str, Any] = ..., **kwargs) -> AsyncContextManager[ClientResponse]: ...
