#!/usr/bin/env python

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload
from zoneinfo import ZoneInfo

import click

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass(slots=True)
class CalVer:
    year: int
    month: int
    patch: int
    dev: int | None

    def next_version(self, *, dev_release: bool = False) -> Self:
        today = datetime.now(tz=ZoneInfo('America/Chicago')).date()
        today_tuple = (today.year - 2000, today.month)

        if today_tuple <= (self.year, self.month):
            year = self.year
            month = self.month
            if self.dev is not None:
                patch = self.patch

                if dev_release:
                    dev = self.dev + 1
                else:
                    dev = None
            else:
                patch = self.patch + 1
                dev = 0 if dev_release else None
        else:
            year = today_tuple[0]
            month = today_tuple[1]
            patch = 0
            dev = 0 if dev_release else None

        return self.__class__(year, month, patch, dev)

    @classmethod
    def parse(cls, version: str, /) -> Self:
        split_version: list[str] = version.split('.')

        return cls(
            year=int(split_version[0]),
            month=int(split_version[1]),
            patch=int(split_version[2]),
            dev=int(split_version[3][3:]) if len(split_version) > 3 else None,
        )

    def __str__(self) -> str:
        version_string = f'{self.year}.{self.month}.{self.patch}'

        if self.dev is not None:
            version_string += f'.dev{self.dev}'

        return version_string


@overload
def run(*args: str, dry_run: Literal[True] = True) -> str: ...


@overload
def run(*args: str, dry_run: bool) -> str | None: ...


def run(*args: str, dry_run: bool = False) -> str | None:
    print(f'> {" ".join(args)}')

    if not dry_run:
        process = subprocess.run(args, capture_output=True, encoding='utf-8')
        return process.stdout[:-1]

    return None


@click.command()
@click.option('--dry-run', is_flag=True)
@click.option('--force', is_flag=True)
def release(dry_run: bool, force: bool) -> None:
    root = Path(__file__).resolve().parent.parent

    with open(root / 'NEWS.md', 'r') as f:
        news_lines = f.readlines()

    if news_lines[0] != '# Version UNRELEASED\n':
        raise RuntimeError('First line must be for unreleased version')

    if not force:
        for line in news_lines[1:]:
            if line.startswith('* '):
                break
            elif line.startswith('# Version '):
                raise RuntimeError('No news entries')

    next_version = CalVer.parse(run('poetry', 'version', '-s')).next_version()

    run('poetry', 'version', str(next_version), dry_run=dry_run)

    print('> Updating NEWS.md')

    news_lines[0] = f'# Version {next_version}\n'

    print(f'>> {news_lines[0][:-1]}')

    if not dry_run:
        with open(root / 'NEWS.md', 'w') as f:
            f.writelines(news_lines)

    run('git', 'add', '--update', '.', dry_run=dry_run)
    run('git', 'commit', '-m', f'Release {next_version}', dry_run=dry_run)
    run('git', 'tag', f'v{next_version}', dry_run=dry_run)
    run(
        'poetry',
        'version',
        str(next_version.next_version(dev_release=True)),
        dry_run=dry_run,
    )

    print('> Updating NEWS.md')

    news_lines = ['# Version UNRELEASED\n', '\n', '\n'] + news_lines

    print(f'>> {news_lines[0][:-1]}')

    if not dry_run:
        with open(root / 'NEWS.md', 'w') as f:
            f.writelines(news_lines)

    run('git', 'add', '--update', '.', dry_run=dry_run)
    run('git', 'commit', '-m', 'Post release version bump', dry_run=dry_run)


if __name__ == '__main__':
    release()
