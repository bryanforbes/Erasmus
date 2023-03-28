from typing import Any, ClassVar

class TimezoneError(ValueError): ...

class NonExistingTime(TimezoneError):
    message: ClassVar[str]
    def __init__(self, dt: Any) -> None: ...

class AmbiguousTime(TimezoneError):
    message: ClassVar[str]
    def __init__(self, dt: Any) -> None: ...
