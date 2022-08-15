from __future__ import absolute_import, unicode_literals

from _typeshed import SupportsItems, SupportsKeysAndGetItem
from collections.abc import Sequence
from typing import Any

from ..syntax.ast import Resource
from .builtins import _FluentFunction
from .errors import FluentFormatError
from .fallback import (
    AbstractResourceLoader as AbstractResourceLoader,
    FluentLocalization as FluentLocalization,
    FluentResourceLoader as FluentResourceLoader,
)
from .resolver import Message, Pattern, TextElement

def FluentResource(source: Any) -> Resource: ...

class FluentBundle:
    locales: Sequence[str]
    use_isolating: bool
    def __init__(
        self,
        locales: Sequence[str],
        functions: SupportsKeysAndGetItem[str, _FluentFunction] = ...,
        use_isolating: bool = ...,
    ) -> None: ...
    def add_resource(self, resource: Resource, allow_overrides: bool = ...) -> None: ...
    def has_message(self, message_id: str) -> bool: ...
    def get_message(self, message_id: str) -> Message: ...
    def format_pattern(
        self, pattern: Pattern | TextElement, args: SupportsItems[str, Any] | None = ...
    ) -> tuple[str, list[FluentFormatError]]: ...
