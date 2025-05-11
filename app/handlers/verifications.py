import random
import time

from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import dp
from app.handlers.booking import create_payment_link
from app.handlers.sessions import FSMClient
from app.services.verifications import send_email_code, send_sms_code



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

            await send_email_code(data['email'], new_email_code)
            await send_sms_code(data['phone'], new_phone_code)

            data.update({
                'booking_email_code': new_email_code,
                'booking_phone_code': new_phone_code,
                'codes_expire': new_expire_time,
                'last_resend_time': current_time
            })

            await message.answer("✅ Новые коды отправлены! Проверьте почту и SMS.")

        except Exception as e:
            await message.answer("❌ Ошибка повторной отправки. Попробуйте позже.")
