from typing import Optional
from collections import namedtuple


class BasicAuth(namedtuple('BasicAuth', ['login', 'password', 'encoding'])):
    def __init__(self, login: str, password: Optional[str] = ...,
                 encoding: Optional[str] = ...) -> None: ...

    def encode(self) -> str: ...

    @staticmethod
    def decode(auth_header: str, encoding: str = 'latin1') -> 'BasicAuth': ...
