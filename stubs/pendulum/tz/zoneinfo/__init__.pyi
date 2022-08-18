from _typeshed import StrOrBytesPath

from .reader import Reader as Reader
from .timezone import Timezone as Timezone

def read(name: str, extend: bool = ...) -> Timezone: ...
def read_file(path: StrOrBytesPath, extend: bool = ...) -> Timezone: ...
