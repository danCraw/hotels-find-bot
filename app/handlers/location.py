from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import dp
from app.keyboards.common import cancel_kb, location_kb
from app.models.city import City, Point
from app.services.geocoding import openrouteservice_city_geocoding, \
    openrouteservice_reverse_geocoding
from .sessions import FSMClient


@dp.message_handler(regexp='Начать', state=None)
@dp.message_handler(regexp='/start', state=None)
async def user_loc(message: types.Message):
    """Start conversation with user"""
    # await FSMClient.point.set()
    markup = location_kb()
    await FSMClient.next()
    await message.answer('Пожалуйста, введите город отправления '
                         'или поделитесь своей геопозицией, нажав на кнопку "📍 Отправить местоположение". '
                         'Чтобы выйти, нажмите или нажмите "Отмена" ', reply_markup=markup)


@dp.message_handler(state=FSMClient.point, content_types=['location'])
async def handle_location(message: types.Message, state: FSMContext):
    """Обработка локации в других состояниях"""
    lat = message.location.latitude
    lon = message.location.longitude
    point = Point(lat=lat, lon=lon)
    city_name = openrouteservice_reverse_geocoding(point)

    async with state.proxy() as data:
        data['city'] = City(
            name=city_name,
            point=point
        )
    await FSMClient.target_city.set()
    await message.answer('📍 Место отправления сохранено!')
    await message.answer('Теперь укажите город назначения:', reply_markup=cancel_kb())


@dp.message_handler(state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext) -> None:
    """Send city to user"""
    async with state.proxy() as data:
        from_coords = openrouteservice_city_geocoding(message.text)
        data['city'] = City(name=message.text, point=from_coords)
    await FSMClient.target_city.set()
    await message.answer('Введите город, в который Вы едете')
