from collections import namedtuple


class BasicAuth(namedtuple('BasicAuth', ['login', 'password', 'encoding'])):
    def __init__(self, login: str, password: str = ...,
                 encoding: str = ...) -> None: ...

    def encode(self) -> str: ...

    @staticmethod
    def decode(auth_header: str, encoding: str = ...) -> 'BasicAuth': ...
