from __future__ import annotations

from logging.handlers import WatchedFileHandler

import uvloop
from botus_receptus import cli

from .erasmus import Erasmus


def main() -> None:
    uvloop.install()
    runner = cli(Erasmus, './config.toml', handler_cls=WatchedFileHandler)
    runner()
