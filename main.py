from aiogram import executor
from create_bot import dp


async def on_startup(_):
    print('The bot has started')


from handlers import client, admin, other
client.client_handler_register(dp)
other.other_handler_register(dp)
if __name__ == '__main__':
    from calculations import *
    vrn_lat, vrn_lon = 51.660781, 39.200296
    sochi_lat, sochi_lon = 43.585472, 39.723098

    path_data = build_route(vrn_lat, vrn_lon, sochi_lat, sochi_lon)
    point = find_coordinates_by_time(27240, path_data)
    find_hotel_by_coordinates(point)


    # executor.start_polling(dp, on_startup=on_startup, skip_updates=True)







