class ExponentialBackoff:
    base: int
    integral: bool

    def __init__(self, base: int = ..., *, integral: bool = ...) -> None: ...

    def delay(self) -> int: ...
