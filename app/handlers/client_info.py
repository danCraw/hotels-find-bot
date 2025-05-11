import random
import re
import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.create_bot import dp
from app.handlers.sessions import FSMClient
from app.services.verifications import send_email_code, send_sms_code


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
        return

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
