import asyncio
import json
from datetime import datetime

import aiogram.utils.markdown as md
import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

from app.create_bot import bot, dp
from app.keyboards import kb_client
from app.models.city import City
from app.models.point import Point
from app.services.geocoding import  openrouteservice_city_geocoding
from .booking import booking_callback
from .sessions import FSMClient
from ..config import OPEN_ROUTE_SERVICE_API_URL, OPEN_ROUTE_SERVICE_API_KEY
from ..services.get_hotels import get_hotel_rooms, find_hotels_by_coordinates
from ..utils import time_from_text_to_seconds, find_coordinates_by_time, \
    cancellation_map


def _build_route(lat_from, lon_from, lat_to, lon_to):
    """Get the route between two points using openrouteservice API"""

    api_url = OPEN_ROUTE_SERVICE_API_URL
    params = {
        'api_key': OPEN_ROUTE_SERVICE_API_KEY,
        'start': f'{lon_from},{lat_from}',
        'end': f'{lon_to},{lat_to}'
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

    features = all_data.get('features', [])
    if not features:
        raise Exception("No features found in the response")

    segments = features[0].get('properties', {}).get('segments', [])
    if not segments:
        raise Exception("No segments found in the response")

    coordinates = features[0].get('geometry', {}).get('coordinates', [])
    length = segments[0].get('distance', 0)  # meters
    duration = segments[0].get('duration', 0)  # seconds
    steps = segments[0].get('steps', [])

    route_data = {
        'coordinates': coordinates,
        'length': length,
        'duration': duration,
        'steps': steps
    }
    return route_data



@dp.message_handler(state=FSMClient.target_city)
async def send_route_data(message: types.Message, state: FSMContext):
    """Send path data to user"""
    async with state.proxy() as data:
        city: City = data.get('city')
        if not city:
            await message.reply('Не удалось определить координаты для города отправления.')
            return

        city_name = city.name
        from_coords: Point = city.point
        to_city = message.text
        to_coords: Point = openrouteservice_city_geocoding(to_city)

        if not to_coords:
            await message.reply('Не удалось определить координаты для города назначения.')
            return

        route_data = _build_route(from_coords.lat, from_coords.lon, to_coords.lat, to_coords.lon)

        if not route_data:
            await message.reply('Не удалось построить маршрут.')
            return

        data['path_data'] = route_data

        time_h_duration = route_data['duration'] // 3600
        time_m_duration = int((route_data['duration'] % 3600) / 60)
        full_length = round(route_data['length'] / 1000)

        await FSMClient.next()
        await bot.send_message(message.from_user.id, md.text(
            md.text("Ваш маршрут:"),
            md.text(f"из: {city_name}"),
            md.text(f"в: {to_city}"),
            md.text(f"протяженностью: {full_length} км,"),
            md.text(f"занимает: {time_h_duration} ч. {time_m_duration} мин."),
            sep='\n'
        ))

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
            reply_markup=keyboard
        )
        await FSMClient.waiting_for_adults.set()


@dp.message_handler(state=FSMClient.travel_time)
async def send_travel_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        original_travel_time = time_from_text_to_seconds(message.text)
        if original_travel_time == 0:
            await message.reply('Пожалуйста, введите данные в верном формате...')
            return

        travel_time = original_travel_time
        found = False
        confirmed_hotels = []
        hotel_rooms_map = {}

        while travel_time >= 0:
            arrival_date = str(datetime.fromtimestamp(message.date.timestamp() + travel_time).date())
            departure_date = str(
                datetime.fromtimestamp(message.date.timestamp() + travel_time + (86400 * data['days_of_stay'])).date())

            point = find_coordinates_by_time(travel_time, data['path_data'])
            hotels = find_hotels_by_coordinates(point)

            adults = data.get('adults')
            children_age = data.get('children_age')
            confirmed_hotels.clear()

            for hotel in hotels:
                hotels_rooms = await get_hotel_rooms(
                    hotel.ya_id,
                    arrival_date,
                    departure_date,
                    adults,
                    children_age
                )

                if hotels_rooms:
                    hotel.rooms = len(hotels_rooms)
                    hotel_rooms_map[hotel.ya_id] = hotels_rooms
                    confirmed_hotels.append(hotel)
                    found = True

            if found:
                break
            else:
                travel_time -= 1800

        if not found:
            await message.reply("К сожалению, не удалось найти подходящие отели.")
            return

        data['travel_time'] = travel_time
        data['confirmed_hotels'] = confirmed_hotels
        data['hotel_rooms_map'] = hotel_rooms_map

        await message.reply("Гостиницы, которые я нашел", reply_markup=kb_client)

        for hotel in confirmed_hotels:

            url = hotel.url if hotel.url else 'отсутствует'
            await message.answer(
                f"🏨 *{hotel.name}*\n"
                f"📍 Адрес: {hotel.address}\n"
                f"🌐 Сайт: {url}\n"
                f"🛏 Свободные номера: {hotel.rooms}",
                parse_mode="Markdown"
            )

            rooms = hotel_rooms_map.get(hotel.ya_id, [])

            for room in rooms:
                price = room['offers'][0]['price']['value'] if room.get('offers') else "?"
                cancellation = room['offers'][0]['cancellation']['refund_type'] if room.get('offers') else "?"
                offer_id = room['offers'][0]['id'] if room.get('offers') else None

                keyboard = InlineKeyboardMarkup()
                if offer_id:
                    callback_data = booking_callback.new(
                        offer_id=offer_id,
                    )
                    keyboard.add(InlineKeyboardButton(
                        "🛎 Забронировать",
                        callback_data=callback_data
                    ))

                message_text = (
                    f"🔹 *{room.get('name', 'Без названия')}*\n"
                    f"💵 Цена: {price} RUB\n"
                    f"📝 Описание: {room.get('description', 'нет описания')}\n"
                    f"🚪 Отмена: {cancellation_map.get(cancellation)}"
                )

                await message.answer(
                    message_text,
                    reply_markup=keyboard
                )
                await asyncio.sleep(0.5)
