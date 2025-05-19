from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import dp
from app.keyboards.common import cancel_kb, location_kb
from app.models.city import City, Point
from app.services.geocoding.osm import (
    openrouteservice_city_geocoding,
    openrouteservice_reverse_geocoding,
)
from .sessions import FSMClient
from ..services.geocoding.db import db_reverse_geocoding, db_city_geocoding
from ..services.geocoding.yandex import yandex_reverse_geocoding, yandex_city_geocoding


@dp.message_handler(regexp="Начать", state=None)
@dp.message_handler(regexp="/start", state=None)
async def user_loc(message: types.Message):
    """Start conversation with user"""
    markup = location_kb()
    await FSMClient.next()
    await message.answer(
        "Пожалуйста, введите город отправления "
        'или поделитесь своей геопозицией, нажав на кнопку "📍 Отправить местоположение". '
        'Чтобы выйти, нажмите или нажмите "Отмена" ',
        reply_markup=markup,
    )


@dp.message_handler(state=FSMClient.point, content_types=["location"])
async def handle_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    point = Point(lat=lat, lon=lon)

    city_name = None
    try:
        city_name = yandex_reverse_geocoding(lon, lat)
    except Exception:
        try:
            city_name = openrouteservice_reverse_geocoding(point)
        except Exception:
            city_name = db_reverse_geocoding(point)

    if not city_name:
        await message.answer(
            "⚠️ Не удалось определить город по полученной геолокации. "
            "Попробуйте указать город вручную."
        )
        return

    async with state.proxy() as data:
        data["city"] = City(name=city_name, point=point)

    await FSMClient.target_city.set()
    await message.answer("📍 Место отправления сохранено!")
    await message.answer("Теперь укажите город назначения:", reply_markup=cancel_kb())


@dp.message_handler(lambda msg: not msg.text.startswith("/"), state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext) -> None:
    city_name = message.text.strip()
    point = None

    try:
        point = yandex_city_geocoding(city_name)
    except Exception:
        try:
            point = openrouteservice_city_geocoding(city_name)
        except Exception:
            point = db_city_geocoding(city_name)

    if not point:
        await message.answer(
            "❗️Местоположение не найдено. Проверьте правильность написания города и попробуйте снова."
        )
        return

    async with state.proxy() as data:
        data["city"] = City(name=city_name, point=point)

    await FSMClient.target_city.set()
    await message.answer("📍 Место отправления сохранено!")
    await message.answer("Введите город, в который Вы едете")
