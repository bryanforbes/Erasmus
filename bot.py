#!/usr/bin/env python

import asyncio
import uvloop
import contextlib
import logging
import click

from erasmus import Erasmus

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@contextlib.contextmanager
def setup_logging(log_to_console: bool, log_level: str):
    try:
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)

        logging.getLogger('erasmus').setLevel(getattr(logging, log_level))

        log = logging.getLogger()
        log.setLevel(logging.INFO)

        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')

        handler = logging.FileHandler(filename='erasmus.log', encoding='utf-8', mode='w')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(fmt)
            log.addHandler(console_handler)

        yield
    finally:
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


@click.command()
@click.option('--log-to-console', is_flag=True)
@click.option('--log-level',
              type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
              default='info')
def main(log_to_console: bool, log_level: str):
    log_level = log_level.upper()

    with setup_logging(log_to_console, log_level):
        bot = Erasmus("./config.ini")
        bot.run()


if __name__ == '__main__':
    main()
