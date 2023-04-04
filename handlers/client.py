import json
from aiogram import types, Dispatcher
from create_bot import bot, dp
from aiogram.types import KeyboardButton
from keyboards import kb_client
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram.utils.markdown as md
from calculations import *


@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id,
                           'Привет, я бот для поиска отелей в дороге. Как я работаю: спрашиваю у Вас текущее местоположение, '
                           'потом город, в который едете, затем Вы можете указать время, через которое хотели бы сделать '
                           'остановку в отеле, я составлю маршрут и рассчитаю примерное место, в котором Вы окажетесь.',
                           reply_markup=kb_client)


''' INFO'''


@dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    await bot.send_message(message.from_user.id, "some info")


'''USER LOCATION'''


class FSMClient(StatesGroup):
    point = State()
    destination_city = State()
    travel_time = State()
    # route_data = State()


@dp.message_handler(commands=['go'], state=None)
async def user_loc(message: types.Message):
    # if LAT is None or LON is None:
    #     await bot.send_message(message.from_user.id,
    #                            'Пожалуйста, введите свое местоположение, нажав на кнопку My location')
    #     return
    await FSMClient.point.set()
    b_location = KeyboardButton('/locate', request_location=True)
    b_cancel = KeyboardButton('/cancel')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(b_location, b_cancel)

    await message.answer('Пожалуйста, введите город отправления '
                         'или поделитесь своей геопозицией, нажав на кнопку  "locate". '
                         'Чтобы выйти, нажмите или введите"cancel" ', reply_markup=markup)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cansel_handler(message: types.Message, state: FSMContext):
    cur_state = await state.get_state()
    if cur_state is None:
        return
    await state.finish()
    await message.reply('отмена')


@dp.message_handler(state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        from_coords = city_geocoding(message.text)
        data['point'] = from_coords
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')

@dp.message_handler(state=FSMClient.point, content_types=['location'])
async def user_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"latitude:{lat}\nlongitude:{lon}"
    async with state.proxy() as data:
        data['point'] = {'lat': lat, 'lon': lon}
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')
    # await bot.send_message(message.from_user.id, coordinates)


@dp.message_handler(state=FSMClient.destination_city)
async def send_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        to_coords = city_geocoding(message.text)
        data['destination_city'] = {'city': message.text, 'lat': to_coords['lat'], 'lon': to_coords['lon']}
    await FSMClient.next()
    await message.reply('Далее введите время (в часах или минутах), через которое хотите остановиться в '
                        'отеле. Например: "3 часа" или "56 минут" или "5 часов 42 минуты".')


@dp.message_handler(state=FSMClient.travel_time)
async def send_travel_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        travel_time = time_from_text_to_seconds(message.text)
        if travel_time == 0:
            await bot.send_message(message.from_user.id, 'Пожалуйста, введите данные в верном формате')
            return
        else:
            data['travel_time'] = travel_time
    async with state.proxy() as data:
        # to_coords = city_geocoding(data['destination_city'])
        path_data = build_route(data['point']['lat'], data['point']['lon'], data['destination_city']['lat'],
                                data['destination_city']['lon'])
        point = find_coordinates_by_time(data['travel_time'], path_data)
        hotels = find_hotel_by_coordinates(point)
        # await bot.send_message(
        #     message.from_user.id,
        #     md.text(
        #         md.text(data['point']),
        #         md.text(data['destination_city']),
        #         md.text(data['travel_time']),
        #         sep='\n',
        #     ), reply_markup=kb_client
        # )
        for hotel in hotels:
            await bot.send_message(message.from_user.id, hotel)
    await state.finish()


# @dp.message_handler(content_types=['location'])
# async def user_location(message: types.Message):
#     lat = message.location.latitude
#     lon = message.location.longitude
#     coordinates = f"latitude:{lat}\nlongitude:{lon}"
#     await bot.send_message(message.from_user.id, coordinates)


def client_handler_register(dp: Dispatcher):
    pass
    # dp.register_message_handler(start_command, commands=['start', 'help'])
    # dp.register_message_handler(get_info, commands=['info'])
    # dp.register_message_handler(user_location, content_types=['location'])
