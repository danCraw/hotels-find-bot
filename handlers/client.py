import asyncio
import random
import re
import time
from datetime import datetime

import aiohttp
from aiogram import types, Dispatcher
from aiogram.utils.callback_data import CallbackData

from create_bot import bot, dp
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
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
from verification import send_email_code, send_sms_code

class BookingStates(StatesGroup):
    GET_EMAIL = State()
    GET_PHONE = State()
    GET_GUEST_COUNT = State()
    GET_GUEST_DATA = State()
    VERIFYING_CODES = State()
    send_payment_msg = State()

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
    client_info = State()
    verifying_codes = State()


@dp.message_handler(regexp='Начать', state=None)
@dp.message_handler(regexp='/start', state=None)
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
    days_of_stay = State()
    client_info = State()
    booking_data = State()

booking_callback = CallbackData("book", "offer_id")

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


@dp.callback_query_handler(booking_callback.filter(), state="*")
async def handle_booking_button(callback: types.CallbackQuery, state: FSMContext):
    _, offer_id = callback.data.split(':')

    async with state.proxy() as data:
        data['offer_id'] = offer_id

    # Отправляем инструкцию
    instruction = (
        "📝 *Введите ваши данные в следующем формате:*\n\n"
        "Телефон: +79123456789\n"
        "Email: example@mail.com\n"
        "1. Иван Иванов\n"
        "2. Мария Иванова\n"
        "3. Пётр Иванов (ребёнок 5 лет)\n\n"
        "_Обратите внимание на формат номеров и порядок данных_"
    )

    await callback.message.answer(instruction, parse_mode="Markdown")
    await callback.answer()

    await FSMClient.client_info.set()


async def create_payment_link(message, data):
    offer = await get_hotel_booking_offer(data['offer_id'])

    booking_token = offer["booking_token"]

    try:
        async with aiohttp.ClientSession() as session:
            order_data = await create_hotel_booking_order(
                booking_token,
                data['email'],
                data['phone'],
                data['guests']
            )

            order_id = order_data['order_id']

            status_data = await get_hotel_booking_status(order_id)

            payment_link = status_data.get('payment_url')

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(
                "💳 Перейти к оплате",
                url=payment_link
            ))

            await message.answer(
                "✅ Заказ создан! Ссылка для оплаты:",
                reply_markup=keyboard
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@dp.callback_query_handler(Text(startswith="book:"))
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
    _, offer_id = callback.data.split(':')

    async with state.proxy() as data:
        data['offer_id'] = offer_id

    data = await state.get_data()

    offer = await get_hotel_booking_offer(data['offer_id'])

    booking_token = offer["booking_token"]

    try:
        async with aiohttp.ClientSession() as session:
            order_data = await create_hotel_booking_order(
                booking_token,
                data['email'],
                data['phone'],
                data['guests']
            )

            order_id = order_data['order_id']

            status_data = await get_hotel_booking_status(order_id)

            payment_link = status_data.get('payment_url')

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(
                "💳 Перейти к оплате",
                url=payment_link
            ))

            await callback.message.answer(
                "✅ Заказ создан! Ссылка для оплаты:",
                reply_markup=keyboard
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await state.finish()


@dp.message_handler(lambda message: message.text == "Отправить коды повторно", state=FSMClient.verifying_codes)
async def resend_verification_codes(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        current_time = int(time.time())
        last_resend = data.get('last_resend_time', 0)

        if current_time - last_resend < 30:
            remaining = 30 - (current_time - last_resend)
            await message.answer(f"⏳ Повторная отправка будет доступна через {remaining} секунд")
            return

        try:
            new_email_code = str(random.randint(100000, 999999))
            new_phone_code = str(random.randint(100000, 999999))
            new_expire_time = current_time + 300  # +5 минут

            # Отправляем новые коды
            await send_email_code(data['email'], new_email_code)
            await send_sms_code(data['phone'], new_phone_code)

            # Обновляем данные в состоянии
            data.update({
                'booking_email_code': new_email_code,
                'booking_phone_code': new_phone_code,
                'codes_expire': new_expire_time,
                'last_resend_time': current_time  # Фиксируем время отправки
            })

            await message.answer("✅ Новые коды отправлены! Проверьте почту и SMS.")

        except Exception as e:
            await message.answer("❌ Ошибка повторной отправки. Попробуйте позже.")


@dp.message_handler(state=FSMClient.client_info)
async def process_client_info(message: types.Message, state: FSMContext):
    booking_info = {
        'phone': None,
        'email': None,
        'guests': []
    }

    try:
        data = message.text.split('\n')

        for line in data:
            line = line.strip().lower()
            if line.startswith('телефон:'):
                booking_info['phone'] = line.split(':', 1)[1].strip()
            elif line.startswith('email:'):
                booking_info['email'] = line.split(':', 1)[1].strip()
            elif line[0].isdigit() and line[1] in '. )':
                guest = line.split('.', 1)[1].strip()
                booking_info['guests'].append(guest)

        if not booking_info['phone'] or not booking_info['email'] or not booking_info['guests']:
            raise ValueError

    except Exception as e:
        await message.answer("Некорректный формат данных. Пожалуйста, введите данные в формате:\n\n"
                             "номер телефона: +79123456789\n"
                             "e-mail: example@mail.com\n"
                             "1. Иван Иванов\n"
                             "2. Мария Иванова\n"
                             "3. Пётр Иванов ребёнок 5 лет")

    if not re.match(r'^\+?[1-9]\d{7,14}$', booking_info['phone']):
        await message.answer("❌ Неверный формат телефона")
        return

    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', booking_info['email']):
        await message.answer("❌ Неверный формат email")
        return

    email_code = str(random.randint(100000, 999999))
    phone_code = str(random.randint(100000, 999999))
    codes_expire = int(time.time()) + 300

    try:
        await send_email_code(booking_info['email'], email_code)
        await send_sms_code(booking_info['phone'], phone_code)
    except Exception as e:
        await message.answer("❌ Ошибка отправки кодов. Проверьте правильность данных и попробуйте снова.")

    async with state.proxy() as data:
        data.update({
            'booking_email_code': email_code,
            'booking_phone_code': phone_code,
            'codes_expire': codes_expire,
            'attempts_left': 3  # Лимит попыток
        })

    await message.answer(
        "📬 Коды подтверждения отправлены на ваш email и телефон.\n\n"
        "Введите коды в формате:\n"
        "Email: 123456\n"
        "Телефон: 654321",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Отправить коды повторно")
        )
    )

    async with state.proxy() as data:
        data.update({
            "phone": booking_info['phone'],
            "email": booking_info['email'],
            "guests": booking_info['guests'],
        })

    await FSMClient.verifying_codes.set()


@dp.message_handler(state=FSMClient.verifying_codes)
async def verify_codes(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if int(time.time()) > data['codes_expire']:
            await message.answer("⌛ Время действия кодов истекло. Запросите новые.")
            return

        data['attempts_left'] -= 1
        if data['attempts_left'] < 0:
            await message.answer("🚫 Превышено количество попыток. Начните процесс заново.")
            await state.finish()
            return

        try:
            input_data = {k.strip().lower(): v.strip()
                          for k, v in (line.split(':', 1)
                                       for line in message.text.split('\n'))}

            email_match = input_data.get('email') == data['booking_email_code']
            phone_match = input_data.get('телефон') == data['booking_phone_code']

            if email_match and phone_match:
                await message.answer("✅ Коды подтверждены! Переходим к созданию заказа ")
                await state.finish()
            else:
                error_msg = "Неверные коды:\n"
                if not email_match:
                    error_msg += "• Email код\n"
                if not phone_match:
                    error_msg += "• SMS код\n"

                await message.answer(
                    f"{error_msg}\n"
                    f"Осталось попыток: {data['attempts_left']}\n"
                    "Попробуйте ещё раз или запросите новые коды."
                )
        except Exception as e:
            await message.answer("❌ Неправильный формат. Используйте:\nEmail: 123456\nТелефон: 654321")

    await create_payment_link(message, data)


@dp.message_handler(state=Filters.waiting_for_adults)
async def process_adults_input(message: types.Message, state: FSMContext):
    try:
        adults = int(message.text)
        if adults <= 0:
            await message.answer("Количество взрослых должно быть положительным числом. Пожалуйста, введите снова:")
            return
        if adults > 20:
            await message.answer("Слишком большое количество взрослых. Максимум 20. Введите снова:")
            return

        await state.update_data(adults=adults)
        await message.answer("Введите количество детей:")
        await Filters.waiting_for_children.set()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (например: 1, 2, 3). Попробуйте снова:")


@dp.message_handler(state=Filters.waiting_for_children)
async def process_children_input(message: types.Message, state: FSMContext):
    try:
        children = int(message.text)
        if children < 0:
            await message.answer("Количество детей не может быть отрицательным. Пожалуйста, введите снова:")
            return
        if children > 10:
            await message.answer("Слишком большое количество детей. Максимум 10. Введите снова:")
            return

        await state.update_data(children=children)
        user_data = await state.get_data()

        if children > 0:
            await message.answer(f"Введите возраст для каждого из {children} детей через запятую (например: 5, 8):")
            await Filters.waiting_for_children_age.set()
        else:
            await message.answer("Сколько дней вы планируете провести в отеле?")
            await Filters.days_of_stay.set()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число детей (например: 0, 1, 2). Попробуйте снова:")


@dp.message_handler(state=Filters.waiting_for_children_age)
async def process_children_age_input(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        children_count = user_data.get('children', 0)

        ages = [age.strip() for age in message.text.split(',')]

        if len(ages) != children_count:
            await message.answer(
                f"Вы указали {len(ages)} возрастов, но детей {children_count}. Пожалуйста, введите ровно {children_count} возраста через запятую:")
            return

        valid_ages = []
        for age in ages:
            try:
                age_int = int(age)
                if age_int <= 0:
                    await message.answer(
                        f"Возраст '{age}' недопустим. Возраст должен быть положительным числом. Введите возрасты снова:")
                    return
                if age_int > 17:
                    await message.answer(
                        f"Возраст '{age}' слишком большой для ребенка. Максимальный возраст ребенка - 17 лет. Введите возрасты снова:")
                    return
                valid_ages.append(age_int)
            except ValueError:
                await message.answer(
                    f"Некорректный возраст '{age}'. Пожалуйста, введите только числа через запятую (например: 5, 8):")
                return

        await state.update_data(children_age=valid_ages)
        await message.answer("Сколько дней вы планируете провести в отеле?")
        await Filters.days_of_stay.set()

    except Exception as e:
        await message.answer(
            "Произошла ошибка при обработке возрастов. Пожалуйста, введите возрасты детей через запятую еще раз:")


@dp.message_handler(state=Filters.days_of_stay)
async def process_days_of_stay(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)

        if days <= 0:
            await message.answer("Количество дней должно быть положительным числом. Пожалуйста, введите снова:")
            return

        if days > 100:
            await message.answer(
                "Слишком большое количество дней. Введите снова:")
            return

        if days < 1:
            await message.answer("Минимальный срок проживания - 1 день. Пожалуйста, введите снова:")
            return

        await state.update_data(days_of_stay=days)

        await message.answer(
            'Далее введите время (в часах или минутах), через которое хотите остановиться в '
            'отеле. Например: "3 часа" или "56 минут" или "5 часов 42 минуты".\n'
            'Пожалуйста, используйте только числа и слова "час/часов/часа" и "минута/минут/минуты".'
        )
        await FSMClient.travel_time.set()

    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное количество дней (целое число).\n"
            "Например: 1, 3, 7, 14 и т.д.\n"
            "Попробуйте снова:"
        )

def client_handler_register(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'])
    dp.register_message_handler(get_info, commands=['info'])
    dp.register_message_handler(user_location, content_types=['location'])
