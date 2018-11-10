import asyncio
import uvloop

from botus_receptus import cli

from .erasmus import Erasmus


def main() -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    runner = cli(Erasmus, './config.toml')
    runner()
