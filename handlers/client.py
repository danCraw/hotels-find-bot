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

from models.city import City
from models.hotel import Hotel
from models.point import Point

''' START '''
@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    """Send welcome message to user"""
    await bot.send_message(message.from_user.id,
                           'Привет, я бот для поиска отелей в дороге. Как я работаю: спрашиваю у Вас текущее местоположение, '
                           'потом город, в который едете, затем Вы можете указать время, через которое хотели бы сделать '
                           'остановку в отеле, я составлю маршрут и рассчитаю примерное место, в котором Вы окажетесь.',
                           reply_markup=kb_client)

''' INFO '''
@dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    """Send info about bot"""
    await bot.send_message(message.from_user.id, md.text(
        md.text("Всё, что Вам нужно указать, чтобы я нашел лучшие отели для Вас:"),
        md.text("* ввести город отправления или указать свою локацию (доступно с мобильного устройства)"),
        md.text("* далее необходимо ввести город назначения"),
        md.text("* и затем ввести время, через которое хотите остановиться в отеле"),
        sep='\n',
    ))

''' USER LOCATION '''
class FSMClient(StatesGroup):
    point = State()
    destination_city = State()
    travel_time = State()

@dp.message_handler(regexp='Начать', state=None)
async def user_loc(message: types.Message):
    """Start conversation with user"""
    await FSMClient.point.set()
    b_location = KeyboardButton('Локация', request_location=True)
    b_cancel = KeyboardButton('Отмена')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(b_location, b_cancel)

    await message.answer('Пожалуйста, введите город отправления '
                         'или поделитесь своей геопозицией, нажав на кнопку "Локация". '
                         'Чтобы выйти, нажмите или нажмите "Отмена" ', reply_markup=markup)

@dp.message_handler(state='*', commands='Отмена')
@dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """Cancel current state and return to the previous one"""
    cur_state = await state.get_state()
    if cur_state is None:
        return
    await state.finish()
    await message.reply('Отмена')

@dp.message_handler(state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext) -> None:
    """Send city to user"""
    async with state.proxy() as data:
        from_coords = yandex_city_geocoding(message.text)
        data['city'] = City(name=message.text, point=from_coords)
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')

@dp.message_handler(state=FSMClient.point, content_types=['location'])
async def user_location(message: types.Message, state: FSMContext):
    """Get user location and send it to user"""
    lat = message.location.latitude
    lon = message.location.longitude
    city_name = yandex_reverse_geocoding(lon=lon, lat=lat)

    async with state.proxy() as data:
        city_point = Point(lat=lat, lon=lon)
        data['city'] = City(name=city_name, point=city_point)

    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')


@dp.message_handler(state=FSMClient.destination_city)
async def send_path_data(message: types.Message, state: FSMContext):
    """Send path data to user"""
    async with state.proxy() as data:
        city: City = data.get('city')
        if not city:
            await message.reply('Не удалось определить координаты для города отправления.')
            return

        city_name = city.name
        from_coords: Point = city.point
        to_city = message.text
        to_coords: Point = yandex_city_geocoding(to_city)

        if not to_coords:
            await message.reply('Не удалось определить координаты для города назначения.')
            return

        route_data = build_route(from_coords.lat, from_coords.lon, to_coords.lat, to_coords.lon)

        if not route_data:
            await message.reply('Не удалось построить маршрут.')
            return

        data['path_data'] = route_data

        time_h_duration = route_data['duration'] // 3600
        time_m_duration = int((route_data['duration'] % 3600) / 60)
        full_length = round(route_data['length'] / 1000, 3)

        await FSMClient.next()
        await bot.send_message(message.from_user.id, md.text(
            md.text("Ваш маршрут:"),
            md.text(f"из: {city_name}"),
            md.text(f"в: {to_city}"),
            md.text(f"протяженностью: {full_length} км,"),
            md.text(f"занимает: {time_h_duration} ч. {time_m_duration} мин."),
            sep='\n'
        ))
        await message.answer(
            "Введите количество взрослых:"
        )
        await Filters.waiting_for_adults.set()


class Filters(StatesGroup):
    waiting_for_adults = State()
    waiting_for_children = State()
    waiting_for_children_age = State()
    waiting_for_pets = State()


@dp.message_handler(state=FSMClient.travel_time)
async def send_travel_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        travel_time = time_from_text_to_seconds(message.text)
        if travel_time == 0:
            await bot.send_message(message.from_user.id, 'Пожалуйста, введите данные в верном формате. Возможно, '
                                                         'Вы пытаетесь отправить боту свою геолокацию, '
                                                         'используя устройство, с которого это сделать нельзя, '
                                                         'например компьютер или ноутбук. В таком случае введите '
                                                         'город отправления самостоятельно')
            return



        point = find_coordinates_by_time(travel_time, data['path_data'])
        hotels: list[Hotel] = find_hotels_by_coordinates(point)
        await FSMClient.next()
        adults = data.get('adults')
        children = data.get('children')

        founded_rooms = []
        ostrovok_hotels = get_ostrovok_hotels(hotels)
        for hotel in ostrovok_hotels:
            hotels_rooms: list[Hotel] = await find_rooms_by_params(hotel["name"], adults, children)
            founded_rooms.append(hotels_rooms)

        await bot.send_message(message.from_user.id, "Гостиницы, которые я нашел", reply_markup=kb_client)

        for hotel in hotels:
            url = hotel.url if hotel.url else 'отсутствует'
            phones = hotel.phones if hotel.phones else 'отсутствуют'
            hours = hotel.hours if hotel.hours else 'отсутствуют'

            await bot.send_message(message.from_user.id, md.text(
                md.text(f'Название: {hotel.name}'),
                md.text(f'Адрес: {hotel.address}'),
                md.text(f'Сайт: {url}'),
                md.text(f'Телефон: {phones}'),
                md.text(f'Часы работы: {hours}'),
                sep='\n',
            ))
            sleep(0.5)




@dp.message_handler(state=Filters.waiting_for_adults)
async def process_adults_input(message: types.Message, state: FSMContext):
    await state.update_data(adults=int(message.text))
    await message.answer("Введите количество детей:")
    await Filters.waiting_for_children.set()


@dp.message_handler(state=Filters.waiting_for_children)
async def process_children_input(message: types.Message, state: FSMContext):
    await state.update_data(children=int(message.text))
    user_data = await state.get_data()
    children_count = user_data.get('children')

    if children_count:
        await message.answer(f"Введите возраст для каждого из {children_count} детей через запятую (например, 5, 8):")
        await Filters.waiting_for_children_age.set()
    else:
        await got_to_count_travel_time(message)


@dp.message_handler(state=Filters.waiting_for_children_age)
async def process_children_age_input(message: types.Message, state: FSMContext):
    ages = message.text.split(',')
    ages = [age.strip() for age in ages]

    await state.update_data(children_age=ages)
    await message.answer("У вас есть питомцы? (да/нет)")
    await got_to_count_travel_time(message)


async def got_to_count_travel_time(message: types.Message):
    await message.answer('Далее введите время (в часах или минутах), через которое хотите остановиться в '
                         'отеле. Например: "3 часа" или "56 минут" или "5 часов 42 минуты".')
    await FSMClient.travel_time.set()


def client_handler_register(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'])
    dp.register_message_handler(get_info, commands=['info'])
    dp.register_message_handler(user_location, content_types=['location'])
