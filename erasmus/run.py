import uvloop

from botus_receptus import cli

from .erasmus import Erasmus


def main() -> None:
    uvloop.install()
    runner = cli(Erasmus, './config.toml')
    runner()
