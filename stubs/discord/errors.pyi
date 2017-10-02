from typing import Optional, Dict, Any, Union
from aiohttp import ClientResponse


class DiscordException(Exception):
    ...


class ClientException(DiscordException):
    ...


class NoMoreItems(DiscordException):
    ...


class GatewayNotFound(DiscordException):
    ...


def flatten_error_dict(d: Dict[str, Any], key: str = ...) -> Dict[str, Any]: ...


class HTTPException(DiscordException):
    response: ClientResponse
    text: str
    status: int
    code: int

    def __init__(self, response: ClientResponse, message: Union[str, Dict[str, Any]]) -> None: ...


class Forbidden(HTTPException):
    ...


class NotFound(HTTPException):
    ...


class InvalidArgument(ClientException):
    ...


class LoginFailure(ClientException):
    ...


class ConnectionClosed(ClientException):
    code: int
    reason: str
    shard_id: Optional[int]

    def __init__(self, original: Exception, *, shard_id: int) -> None: ...
