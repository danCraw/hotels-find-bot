from aiogram import types, utils, executor
from create_bot import dp

from geopy.geocoders import Yandex
from config import TOKEN, YANDEX_API

geolocator = Yandex(YANDEX_API)

async def on_startup(_):
    print('The bot has started')


from handlers import client, admin, other

client.client_handler_register(dp)

other.other_handler_register(dp)  # ниже всех других handler's

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
