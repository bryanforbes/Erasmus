from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, type_check_only
from typing_extensions import Literal, Protocol

from .dammit import EntitySubstitution as EntitySubstitution
from .element import Tag

# TODO: remove this comment when a new version of black comes out
@type_check_only
class _EntitySubstitutionCallback(Protocol):
    def __call__(self, __value: str) -> str: ...

class Formatter(EntitySubstitution):
    XML_FORMATTERS: ClassVar[Dict[str, Formatter]]
    HTML_FORMATTERS: ClassVar[Dict[str, Formatter]]
    HTML: ClassVar[Literal['html']]
    XML: ClassVar[Literal['xml']]
    HTML_DEFAULTS: Dict[str, Set[str]]
    language: Optional[Literal['html', 'xml']]
    entity_substitution: Optional[_EntitySubstitutionCallback]
    void_element_close_prefix: Any = ...
    cdata_containing_tags: Any = ...
    def __init__(
        self,
        language: Optional[Literal['html', 'xml']] = ...,
        entity_substitution: Optional[_EntitySubstitutionCallback] = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: Optional[List[str]] = ...,
    ) -> None: ...
    def substitute(self, ns: str) -> str: ...
    def attribute_value(self, value: str) -> str: ...
    def attributes(self, tag: Tag) -> List[Tuple[str, str]]: ...

class HTMLFormatter(Formatter):
    REGISTRY: ClassVar[Dict[str, HTMLFormatter]]
    def __init__(
        self,
        entity_substitution: Optional[_EntitySubstitutionCallback] = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: Optional[List[str]] = ...,
    ) -> None: ...

class XMLFormatter(Formatter):
    REGISTRY: ClassVar[Dict[str, XMLFormatter]]
    def __init__(
        self,
        entity_substitution: Optional[_EntitySubstitutionCallback] = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: Optional[List[str]] = ...,
    ) -> None: ...
