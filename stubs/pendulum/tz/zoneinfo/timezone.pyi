from .posix_timezone import PosixTimezone
from .transition import Transition

class Timezone:
    def __init__(
        self,
        transitions: list[Transition],
        posix_rule: PosixTimezone | None = ...,
        extended: bool = ...,
    ) -> None: ...
    @property
    def transitions(self) -> list[Transition]: ...
    @property
    def posix_rule(self) -> PosixTimezone | None: ...
