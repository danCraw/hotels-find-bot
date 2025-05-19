import aiohttp
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from app.create_bot import dp
from app.handlers.sessions import FSMClient
from app.utils import (
    get_hotel_booking_offer,
    get_hotel_booking_status,
    create_hotel_booking_order,
)

booking_callback = CallbackData("book", "offer_id")


@dp.callback_query_handler(booking_callback.filter(), state="*")
async def handle_booking_button(callback: types.CallbackQuery, state: FSMContext):
    _, offer_id = callback.data.split(":")

    async with state.proxy() as data:
        data["offer_id"] = offer_id

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
    offer = await get_hotel_booking_offer(data["offer_id"])

    booking_token = offer["booking_token"]

    try:
        async with aiohttp.ClientSession():
            order_data = await create_hotel_booking_order(
                booking_token, data["email"], data["phone"], data["guests"]
            )

            order_id = order_data["order_id"]

            status_data = await get_hotel_booking_status(order_id)

            payment_link = status_data.get("payment_url")

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("💳 Перейти к оплате", url=payment_link))

            await message.answer(
                "✅ Заказ создан! Ссылка для оплаты:", reply_markup=keyboard
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@dp.callback_query_handler(Text(startswith="book:"))
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
    _, offer_id = callback.data.split(":")

    async with state.proxy() as data:
        data["offer_id"] = offer_id

    data = await state.get_data()

    offer = await get_hotel_booking_offer(data["offer_id"])

    booking_token = offer["booking_token"]

    try:
        async with aiohttp.ClientSession():
            order_data = await create_hotel_booking_order(
                booking_token, data["email"], data["phone"], data["guests"]
            )

            order_id = order_data["order_id"]

            status_data = await get_hotel_booking_status(order_id)

            payment_link = status_data.get("payment_url")

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("💳 Перейти к оплате", url=payment_link))

            await callback.message.answer(
                "✅ Заказ создан! Ссылка для оплаты:", reply_markup=keyboard
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await state.finish()
