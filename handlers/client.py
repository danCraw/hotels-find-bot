import json
import time

from aiogram import types, Dispatcher
from create_bot import bot, dp
from aiogram.types import KeyboardButton
from keyboards import kb_client
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram.utils.markdown as md
from calculations import *
from time import sleep


''' START '''
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
    await bot.send_message(message.from_user.id, md.text(
        md.text("Всё, что Вам нужно указать, чтобы я нашел лучшие  отели для Вас:"),
        md.text("* ввести город отправления или указать свою локацию (доступно с мобильного устройства)"),
        md.text("* далее необходимо ввести город назначения"),
        md.text("* и затем ввести время, через которое хотите остановиться в отеле"),
        sep='\n',
    ))

'''USER LOCATION'''


class FSMClient(StatesGroup):
    point = State()
    path_data = State()
    travel_time = State()

@dp.message_handler(commands=['go'], state=None)
async def user_loc(message: types.Message):
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
    await message.reply('cancel')


@dp.message_handler(state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        from_coords = yandex_city_geocoding(message.text)
        data['point'] = {'city': message.text, 'lat': from_coords['lat'], 'lon': from_coords['lon']}
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')


@dp.message_handler(state=FSMClient.point, content_types=['location'])
async def user_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    city = yandex_reverse_geocoding(lon=lon, lat=lat)
    # coordinates = f"latitude:{lat}\nlongitude:{lon}"
    async with state.proxy() as data:
        data['point'] = {'city': city, 'lat': lat, 'lon': lon}
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')
    # await bot.send_message(message.from_user.id, coordinates)


@dp.message_handler(state=FSMClient.path_data)
async def send_path_data(message: types.Message, state: FSMContext):
    city = {}
    async with state.proxy() as data:
        to_coords = yandex_city_geocoding(message.text)
        city['destination_city'] = {'city': message.text, 'lat': to_coords['lat'], 'lon': to_coords['lon']}

        data['path_data'] = build_route(data['point']['lat'], data['point']['lon'], city['destination_city']['lat'],
                                        city['destination_city']['lon'])
        # time_duration = time.strftime("%H:%M", time.gmtime(data['path_data']['duration']))
        # time_duration = time_duration.split(':')
        time_h_duration = data['path_data']['duration'] // 3600
        time_m_duration = int((data['path_data']['duration'] / 3600 - time_h_duration) * 60)
        full_length = round(data['path_data']['length'] / 1000, 3)
    await FSMClient.next()
    await bot.send_message(message.from_user.id, md.text(
        md.text(f"Ваш маршрут:"),
        md.text(f"из: {data['point']['city']}"),
        md.text(f"в: {city['destination_city']['city']}"),
        md.text(f"протяженностью: {full_length} км,"),
        md.text(f"занимает: {time_h_duration} ч. {time_m_duration} мин."),
        sep='\n'
    ))
    await message.reply('Далее введите время (в часах или минутах), через которое хотите остановиться в '
                        'отеле. Например: "3 часа" или "56 минут" или "5 часов 42 минуты".')


@dp.message_handler(state=FSMClient.travel_time)
async def send_travel_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        travel_time = time_from_text_to_seconds(message.text)
        data['travel_time'] = travel_time
        if travel_time == 0:
            await bot.send_message(message.from_user.id, 'Пожалуйста, введите данные в верном формате. Возможно, '
                                                         'Вы пытаетесь отправить боту свою геолокацию, '
                                                         'используя устройство, с которого это сделать нельзя, '
                                                         'например компьютер или ноутбук. В таком случае введите '
                                                         'город отправления самостоятельно')
            return
        point = find_coordinates_by_time(data['travel_time'], data['path_data'])
        # sleep(3)
        hotels = find_hotel_by_coordinates(point)
        await bot.send_message(message.from_user.id, "Гостиницы, которые я нашел", reply_markup=kb_client)
        for hotel in hotels:
            url = hotel['url'] if 'url' in hotel else 'отсутствует'
            phones = hotel['phones'] if 'phones' in hotel else 'отсутствуют'
            hours = hotel['hours'] if 'hours' in hotel else 'отсутствуют'
            await bot.send_message(message.from_user.id, md.text(
                md.text(f'Название: {hotel["name"]}'),
                md.text(f'Адрес: {hotel["address"]}'),
                md.text(f'Сайт: {url}'),
                md.text(f'Телефон: {phones}'),
                md.text(f'Часы работы: {hours}'),
                sep='\n',
            ))
            sleep(0.5)
    await state.finish()


def client_handler_register(dp: Dispatcher):
    pass
    # dp.register_message_handler(start_command, commands=['start', 'help'])
    # dp.register_message_handler(get_info, commands=['info'])
    # dp.register_message_handler(user_location, content_types=['location'])
