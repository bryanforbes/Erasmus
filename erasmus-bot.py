#!/usr/bin/env python

import asyncio
import uvloop

from botus_receptus import cli

from erasmus import Erasmus

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


if __name__ == '__main__':
    runner = cli(Erasmus, './config.ini')
    runner()
