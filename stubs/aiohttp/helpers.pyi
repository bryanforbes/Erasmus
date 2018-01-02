from collections import namedtuple
from typing import TypeVar, Coroutine

_RT = TypeVar('_RT')


class _BaseCoroMixin(Coroutine[None, None, _RT]):
    ...


class BasicAuth(namedtuple('BasicAuth', ['login', 'password', 'encoding'])):
    def __init__(self, login: str, password: str = ...,
                 encoding: str = ...) -> None: ...

    def encode(self) -> str: ...

    @staticmethod
    def decode(auth_header: str, encoding: str = ...) -> 'BasicAuth': ...
