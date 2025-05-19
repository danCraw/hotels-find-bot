import json
from datetime import datetime, date

import aiogram.utils.markdown as md
import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.callback_data import CallbackData

from app.create_bot import bot, dp
from app.keyboards import kb_client
from app.models.city import City
from app.models.point import Point
from .sessions import FSMClient
from ..config import (
    OPEN_ROUTE_SERVICE_API_URL,
    OPEN_ROUTE_SERVICE_API_KEY,
    YANDEX_SEARCH_ORGANIZATION_API,
    YANDEX_GEOCODE_API_KEY,
)
from ..models.hotel import Hotel, OstrovokHotel
from ..services.geocoding.osm import openrouteservice_city_geocoding
from ..services.get_hotels.base import BaseHotelAPI
from ..services.get_hotels.open_street_map import OSMHotelAPI
from ..services.get_hotels.ostrovok import OstrovokHotelAPI
from ..services.get_hotels.yandex import YandexHotelAPI
from ..utils import time_from_text_to_seconds, find_coordinates_by_time


show_rooms_callback = CallbackData("show_rooms", "hotel_id")
more_hotels_callback = CallbackData("more_hotels", "index")


yandex_api = YandexHotelAPI(
    api_key=YANDEX_SEARCH_ORGANIZATION_API, oauth_token=YANDEX_GEOCODE_API_KEY
)
ostrovok_api = OstrovokHotelAPI(
    api_key="08d64714-763a-4d65-9945-c036c465635f", key_id="12839"
)
osm_api = OSMHotelAPI()


def _build_route(lat_from, lon_from, lat_to, lon_to):
    """Get the route between two points using openrouteservice API"""

    api_url = OPEN_ROUTE_SERVICE_API_URL
    params = {
        "api_key": OPEN_ROUTE_SERVICE_API_KEY,
        "start": f"{lon_from},{lat_from}",
        "end": f"{lon_to},{lat_to}",
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {e}")

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    features = all_data.get("features", [])
    if not features:
        raise Exception("No features found in the response")

    segments = features[0].get("properties", {}).get("segments", [])
    if not segments:
        raise Exception("No segments found in the response")

    coordinates = features[0].get("geometry", {}).get("coordinates", [])
    length = segments[0].get("distance", 0)  # meters
    duration = segments[0].get("duration", 0)  # seconds
    steps = segments[0].get("steps", [])

    route_data = {
        "coordinates": coordinates,
        "length": length,
        "duration": duration,
        "steps": steps,
    }
    return route_data


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.target_city
)
async def send_route_data(message: types.Message, state: FSMContext):
    """Send path data to user"""
    async with state.proxy() as data:
        city: City = data.get("city")
        if not city:
            await message.reply(
                "Не удалось определить координаты для города отправления."
            )
            return

        city_name = city.name
        from_coords: Point = city.point
        to_city = message.text
        to_coords: Point = openrouteservice_city_geocoding(to_city)

        if not to_coords:
            await message.reply(
                "Не удалось определить координаты для города назначения."
            )
            return

        route_data = _build_route(
            from_coords.lat, from_coords.lon, to_coords.lat, to_coords.lon
        )

        if not route_data:
            await message.reply("Не удалось построить маршрут.")
            return

        data["path_data"] = route_data

        time_h_duration = route_data["duration"] // 3600
        time_m_duration = int((route_data["duration"] % 3600) / 60)
        full_length = round(route_data["length"] / 1000)

        await FSMClient.next()
        await bot.send_message(
            message.from_user.id,
            md.text(
                md.text("Ваш маршрут:"),
                md.text(f"из: {city_name}"),
                md.text(f"в: {to_city}"),
                md.text(f"протяженностью: {full_length} км,"),
                md.text(f"занимает: {time_h_duration} ч. {time_m_duration} мин."),
                sep="\n",
            ),
        )

        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=4,
        )

        keyboard.add(
            KeyboardButton("1"),
            KeyboardButton("2"),
            KeyboardButton("3"),
            KeyboardButton("4"),
        )

        await message.answer(
            "Выберите количество взрослых или введите свой вариант:",
            reply_markup=keyboard,
        )
        await FSMClient.waiting_for_adults.set()


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.travel_time
)
async def send_travel_time(message: types.Message, state: FSMContext):
    search_message = await message.reply("🔍 Ищем подходящие отели...")

    async with state.proxy() as data:
        original_travel_time = time_from_text_to_seconds(message.text)
        if original_travel_time == 0:
            await message.reply("Пожалуйста, введите данные в верном формате...")
            await search_message.delete()
            return

        travel_time = original_travel_time
        found = False
        confirmed_hotels = []

        while travel_time >= 0:
            arrival_date = datetime.fromtimestamp(
                message.date.timestamp() + travel_time
            ).date()
            departure_date = datetime.fromtimestamp(
                message.date.timestamp() + travel_time + (86400 * data["days_of_stay"])
            ).date()

            point = find_coordinates_by_time(travel_time, data["path_data"])
            adults = data.get("adults")
            children_age = data.get("children_age")
            confirmed_hotels.clear()

            # Попытка получить отели от разных API в порядке приоритета
            api_attempts = [
                ("Yandex", yandex_api),
                ("Ostrovok", ostrovok_api),
                ("OSM", osm_api),
            ]

            for api_name, api_client in api_attempts:
                try:
                    hotels = await _try_get_hotels(
                        api_client,
                        ostrovok_api,  # Передаем ostrovok_api для поиска комнат
                        point,
                        arrival_date,
                        departure_date,
                        adults,
                        children_age,
                        api_name == "OSM",
                    )

                    if hotels:
                        found = True
                        confirmed_hotels.extend(hotels)
                        break  # Переходим к обработке найденных отелей

                except Exception as e:
                    print(f"Ошибка при запросе к {api_name} API: {e}")
                    continue  # Пробуем следующий API

            if found:
                break
            else:
                travel_time -= 1800  # Уменьшаем время на 30 минут и пробуем снова

        try:
            await search_message.delete()
        except Exception as e:
            print(f"Error deleting search message: {e}")

        if not found:
            await message.reply("К сожалению, не удалось найти подходящие отели.")
            return

        confirmed_hotels.sort(key=lambda x: (-getattr(x, "stars", 0), x.avg_price))

        data["all_hotels"] = confirmed_hotels
        data["current_hotel_index"] = 0
        data["travel_time"] = travel_time

        await show_hotels_batch(message, data)


async def _try_get_hotels(
    api_client: BaseHotelAPI,
    ostrovok_api: OstrovokHotelAPI,
    point: Point,
    arrival_date: date,
    departure_date: date,
    adults: int,
    children_age: list,
    is_osm_request: bool = False,
) -> list[Hotel]:
    """Пытается получить отели через указанный API клиент"""
    hotels = []

    found_hotels = api_client.search_hotels_by_geo(
        point=point, checkin=arrival_date, checkout=departure_date
    )

    for hotel in found_hotels:
        try:
            rooms = []

            if is_osm_request:
                ostrovok_hotel = _find_ostrovok_hotel_by_address(
                    ostrovok_api, hotel.address
                )
                if ostrovok_hotel:
                    rooms = ostrovok_api.get_hotel_rooms(
                        hotel_id=ostrovok_hotel.ostrovok_id,
                        checkin_date=arrival_date,
                        checkout_date=departure_date,
                        adults=adults,
                        children_ages=children_age,
                    )
                hotel = ostrovok_hotel
            else:
                hotel_id = (
                    getattr(hotel, "ostrovok_id", None)
                    or getattr(hotel, "ya_id", None)
                    or None
                )
                if hotel_id:
                    rooms = api_client.get_hotel_rooms(
                        hotel_id=hotel_id,
                        checkin_date=arrival_date,
                        checkout_date=departure_date,
                        adults=adults,
                        children_ages=children_age,
                    )

            if rooms:
                total_price = 0
                room_count = 0
                for room in rooms:
                    price = float(room.get("price", 0))
                    if price > 0:
                        total_price += price
                        room_count += 1

                avg_price = total_price / room_count if room_count > 0 else 0
                setattr(hotel, "avg_price", avg_price)
                setattr(hotel, "rooms", rooms)
                hotels.append(hotel)

        except Exception as e:
            print(f"Ошибка при получении комнат для отеля {hotel.name}: {e}")
            continue

    return hotels


def _find_ostrovok_hotel_by_address(
    ostrovok_api: OstrovokHotelAPI, address: str
) -> OstrovokHotel | None:
    try:
        ostrovok_hotel = ostrovok_api.search_hotels_by_address(address)
        if ostrovok_hotel:
            return ostrovok_hotel

    except Exception as e:
        print(f"Ошибка при поиске отеля в Ostrovok по адресу {address}: {e}")

    return None


async def show_hotels_batch(message: types.Message, data: dict, batch_size=3):
    start_index = data["current_hotel_index"]
    end_index = start_index + batch_size
    hotels = data["all_hotels"][start_index:end_index]

    if not hotels:
        await message.answer("Больше отелей не найдено")
        return

    await message.answer(
        "🏨 Найденные отели (лучшие предложения)", reply_markup=kb_client
    )

    for hotel in hotels:
        url = hotel.url if hasattr(hotel, "url") and hotel.url else "не указан"
        stars = "⭐" * getattr(hotel, "stars", 0)

        msg_text = (
            f"🏨 *{hotel.name}* {stars}\n"
            f"📍 Адрес: {getattr(hotel, 'address', 'не указан')}\n"
            f"🌐 Сайт: {url}\n"
            f"💵 Средняя цена: {hotel.avg_price:.2f} RUB\n"
            f"🛏 Доступно номеров: {len(hotel.rooms)}"
        )

        keyboard = InlineKeyboardMarkup()
        if isinstance(hotel, OstrovokHotel):
            callback_data = show_rooms_callback.new(hotel_id=hotel.ostrovok_id)
        else:
            callback_data = show_rooms_callback.new(hotel_id=hotel.ya_id)

        keyboard.add(
            InlineKeyboardButton("🔍 Показать номера", callback_data=callback_data)
        )

        await message.answer(msg_text, reply_markup=keyboard, parse_mode="Markdown")

    if end_index < len(data["all_hotels"]):
        keyboard = InlineKeyboardMarkup()
        callback_data = more_hotels_callback.new(index=end_index)
        keyboard.add(
            InlineKeyboardButton("🔽 Показать ещё отели", callback_data=callback_data)
        )

        await message.answer("Хотите увидеть больше вариантов?", reply_markup=keyboard)


@dp.callback_query_handler(show_rooms_callback.filter(), state=FSMClient.travel_time)
async def show_hotel_rooms(
    callback: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    hotel_id = callback_data["hotel_id"]
    async with state.proxy() as data:
        # Находим отель в списке
        hotel = next((h for h in data["all_hotels"] if h.ostrovok_id == hotel_id), None)

        if not hotel:
            await callback.answer("Отель не найден")
            return

        await callback.answer()
        await callback.message.answer(f"🏨 Номера в отеле {hotel.name}:")

        for room in hotel.rooms[:5]:  # Показываем первые 5 номеров
            room_type = room.get("room_type", "Тип номера не указан")
            bed_type = room.get("bed_type", "Тип кровати не указан")
            price = room.get("price", "?")
            currency = room.get("currency", "RUB")
            meal = room.get("meal", "nomeal")
            rate_hash = room.get("rate_hash", "")

            # Обработка политики отмены
            cancellation_policy = room.get("cancellation_policy", {})
            policies = cancellation_policy.get("policies", [])
            cancellation_text = "Бесплатная отмена: Нет"

            if policies:
                penalty = policies[0].get("penalty", "0")
                if penalty == "0":
                    cancellation_text = "✅ Бесплатная отмена"
                else:
                    cancellation_text = f"❌ Отмена с штрафом: {penalty} {currency}"

            meal_map = {
                "nomeal": "Без питания",
                "breakfast": "Завтрак включён",
                "halfboard": "Полупансион",
                "fullboard": "Полный пансион",
                "allinclusive": "Всё включено",
            }
            meal_description = meal_map.get(meal, "Питание не указано")

            keyboard = InlineKeyboardMarkup()
            if rate_hash:  # Если есть rate_hash, добавляем кнопку бронирования
                booking_url = f"https://ostrovok.ru/orders/reserve/{rate_hash}"
                keyboard.add(InlineKeyboardButton("🛎 Забронировать", url=booking_url))

            message_text = (
                f"🏠 *{room_type}*\n"
                f"🛏 {bed_type}\n"
                f"💵 Цена за ночь: {price} {currency}\n"
                f"🍽 {meal_description}\n"
                f"📝 {cancellation_text}"
            )

            await callback.message.answer(
                message_text, reply_markup=keyboard, parse_mode="Markdown"
            )


@dp.callback_query_handler(more_hotels_callback.filter(), state=FSMClient.travel_time)
async def show_more_hotels(
    callback: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    async with state.proxy() as data:
        data["current_hotel_index"] = int(callback_data["index"])
        await show_hotels_batch(callback.message, data)
        await callback.answer()
