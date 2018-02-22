import asyncio
from typing import Dict, Mapping, Iterable, Callable, Union, AsyncContextManager, Any, Optional, TypeVar, IO
from .connector import BaseConnector
from .abc import AbstractCookieJar
from .helpers import BasicAuth, _BaseCoroMixin
from .client_reqrep import ClientResponse


_RT = TypeVar('_RT')


class _BaseRequestContextManager(_BaseCoroMixin[_RT]):
    ...


class _RequestContextManager(_BaseRequestContextManager[_RT], AsyncContextManager[_RT]):
    ...


class ClientSession(AsyncContextManager['ClientSession']):
    def __init__(self, *, connector: BaseConnector = ...,
                 loop: asyncio.AbstractEventLoop = ...,
                 cookies: Dict[str, str] = ...,
                 headers: Mapping[str, str] = ...,
                 skip_auto_headers: Iterable[str] = ...,
                 auth: BasicAuth = ...,
                 version: str = ...,
                 cookie_jar: AbstractCookieJar = ...,
                 json_serialize: Callable[..., str] = ...,
                 raise_for_status: bool = ...,
                 read_timeout: float = ...,
                 conn_timeout: Union[None, float] = ...) -> None: ...

    def get(self, url: str, *, allow_redirects: bool = ..., **kwargs) -> _RequestContextManager[ClientResponse]: ...

    def post(self, url: str, *, data: Union[Optional[Dict[str, Any]], bytes, str, IO] = ..., **kwargs) -> \
        _RequestContextManager[ClientResponse]: ...

    async def close(self): ...
