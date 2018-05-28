#!/usr/bin/env python

import asyncio
import uvloop

from botus_receptus import run

from erasmus import Erasmus

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


if __name__ == '__main__':
    run(Erasmus, './config.ini')
