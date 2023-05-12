import time

from aiogram import executor
from create_bot import dp


async def on_startup(_):
    print('The bot has started')


from handlers import client, admin, other

client.client_handler_register(dp)
other.other_handler_register(dp)

from calculations import *

if __name__ == '__main__':
    # print(yandex_reverse_geocoding(lon=39.200296, lat=51.660781))

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
