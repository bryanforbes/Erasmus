from typing import Sized, Iterable, Mapping
from http.cookies import SimpleCookie


class AbstractCookieJar(Sized, Iterable):
    def update_cookies(self, cookies: Mapping[str, str],
                       response_url: str = None) -> None: ...

    def filter_cookies(self,
                       response_url: str) -> SimpleCookie: ...
