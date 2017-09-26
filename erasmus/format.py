from typing import Callable


def pluralizer(word: str, suffix: str = 's') -> Callable[[int], str]:
    def pluralize(value: int) -> str:
        result = f'{value} {word}'

        if value == 0 or value > 1:
            result = f'{result}{suffix}'

        return result

    return pluralize
