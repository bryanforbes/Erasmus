# Inspired by https://github.com/TehShrike/regex-fun

from typing import Callable, Pattern, AnyStr, cast, Union, Iterator, Iterable
from mypy_extensions import VarArg, DefaultNamedArg
from functools import partial
import re

_ReOrStrType = Union[str, Pattern[AnyStr]]
_ReOrStrFuncType = Callable[[VarArg(_ReOrStrType)], str]
_ReOrStrGreedyFuncType = Callable[[VarArg(_ReOrStrType), DefaultNamedArg(bool, 'greedy')], str]

A = re.A
ASCII = re.ASCII
DEBUG = re.DEBUG
I = re.I  # noqa: E741
IGNORECASE = re.IGNORECASE
L = re.L
LOCALE = re.LOCALE
M = re.M
MULTILINE = re.MULTILINE
S = re.S
DOTALL = re.DOTALL
X = re.X
VERBOSE = re.VERBOSE


def compile(*args: _ReOrStrType, flags: int = 0) -> Pattern[AnyStr]:
    return re.compile(combine(*args), flags=flags)  # type: ignore


def _to_str(reOrStr: _ReOrStrType) -> str:
    if isinstance(reOrStr, str):
        return reOrStr
    else:
        return str(reOrStr.pattern)


def combine(*args: _ReOrStrType, joiner: str = '') -> str:
    return joiner.join(map(_to_str, args))


def group(*args: _ReOrStrType, start: str = '(?:', joiner: str = '') -> str:
    return start + combine(*args, joiner=joiner) + ')'


capture = cast(_ReOrStrFuncType, partial(group, start='('))
either = cast(_ReOrStrFuncType, partial(group, joiner='|'))


def named_group(name: str) -> Callable[[VarArg(_ReOrStrType), DefaultNamedArg(str, 'joiner')], str]:
    def grouper(*args: _ReOrStrType, joiner: str = '') -> str:
        return group(*args, start=f'(?P<{name}>', joiner=joiner)

    return grouper


def atomic(string: str) -> str:
    if string[0] == '(' and string[-1] == ')':
        return string
    else:
        return group(string)


def _suffix(*args: _ReOrStrType, suffix: str, greedy: bool = True) -> str:
    return f'{atomic(combine(*args))}{suffix}{"" if greedy else "?"}'


optional = cast(_ReOrStrGreedyFuncType, partial(_suffix, suffix='?'))
one_or_more = cast(_ReOrStrGreedyFuncType, partial(_suffix, suffix='+'))
any_number_of = cast(_ReOrStrGreedyFuncType, partial(_suffix, suffix='*'))


def exactly(n: int, *args: _ReOrStrType, greedy: bool = True) -> str:
    return _suffix(*args, suffix=f'{{n}}', greedy=greedy)


def at_least(n: int, *args: _ReOrStrType, greedy: bool = True) -> str:
    return _suffix(*args, suffix=f'{{{n},}}', greedy=greedy)


def between(n: int, m: int, *args: _ReOrStrType, greedy: bool = True) -> str:
    return _suffix(*args, suffix=f'{{{n},{m}}}', greedy=greedy)


escape = re.escape


def escape_all(patterns: Iterable[Union[str, Pattern[AnyStr]]]) -> Iterator[str]:
    for pattern in patterns:
        if isinstance(pattern, str):
            yield re.escape(pattern)
        else:
            yield pattern.pattern  # type: ignore


START = '^'
END = '$'
BACKSLASH = '\\'
METACHARACTERS = r'.^$*+?{}[]\|()-'
DIGIT = DIGITS = r'\d'
WHITESPACE = r'\s'
ALPHANUMERIC = ALPHANUMERICS = r'\w'
ALPHA = ALPHAS = A_TO_Z = r'[a-zA-Z]'
IDENTIFIER = r'[a-zA-Z_][\w_]*'
WORD_BOUNDARY = r'\b'
DOT = r'\.'
UNDERSCORE = r'_'
DASH = r'\-'
ANYTHING = r'.*'
ANY_CHARACTER = r'.'
NEWLINE = r'\\n'
TAB = r'\\t'
LEFT_BRACKET = r'\['
RIGHT_BRACKET = r'\]'
