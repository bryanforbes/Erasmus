import asyncio
import uvloop

from erasmus import Erasmus

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

bot = Erasmus("./config.json")

if __name__ == '__main__':
    bot.run()
