from __future__ import annotations

from typing import Final

_roman_pairs: Final = tuple(
    zip(
        ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'),
        (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    )
)


def int_to_roman(number: int) -> str:
    numerals: list[str] = []

    for letter, value in _roman_pairs:
        count, number = divmod(number, value)
        numerals.append(letter * count)

    return ''.join(numerals)


def roman_to_int(numerals: str) -> int:
    numerals = numerals.upper()
    index = result = 0

    for letter, value in _roman_pairs:
        while numerals[index : index + len(letter)] == letter:
            result += value
            index += len(letter)

    return result
