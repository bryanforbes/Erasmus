from ..period import Period

class DifferenceFormatter:
    def __init__(self, locale: str = ...) -> None: ...
    def format(
        self,
        diff: Period,
        is_now: bool = ...,
        absolute: bool = ...,
        locale: str | None = ...,
    ) -> str: ...
