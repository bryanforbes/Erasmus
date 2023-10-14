from __future__ import annotations

from logging.handlers import WatchedFileHandler

import uvloop
from botus_receptus import cli

from .erasmus import Erasmus


def main() -> None:
    uvloop.install()  # pyright: ignore[reportGeneralTypeIssues, reportUnknownMemberType]
    runner = cli(Erasmus, './config.toml', handler_cls=WatchedFileHandler)
    runner()
