from typing import Sized, Iterable, Mapping, Optional
from http.cookies import SimpleCookie


class AbstractCookieJar(Sized, Iterable[SimpleCookie]):
    def update_cookies(self, cookies: Mapping[str, str],
                       response_url: Optional[str] = ...) -> None: ...

    def filter_cookies(self,
                       response_url: str) -> SimpleCookie: ...
