class FormattableMixin:
    def format(self, fmt: str, locale: str | None = ...) -> str: ...
    def for_json(self) -> str: ...
    def __format__(self, format_spec: str) -> str: ...