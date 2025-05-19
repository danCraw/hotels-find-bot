from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.create_bot import dp
from app.handlers.sessions import FSMClient


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.waiting_for_adults
)
async def process_adults_input(message: types.Message, state: FSMContext):
    try:
        adults = int(message.text)
        if adults <= 0:
            await message.answer(
                "Количество взрослых должно быть положительным числом. Пожалуйста, введите снова:"
            )
            return
        if adults > 20:
            await message.answer(
                "Слишком большое количество взрослых. Максимум 20. Введите снова:"
            )
            return

        await state.update_data(adults=adults)

        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=4,
        )

        keyboard.add(
            KeyboardButton("0"),
            KeyboardButton("1"),
            KeyboardButton("2"),
            KeyboardButton("3"),
        )

        await message.answer(
            "Выберите количество детей или введите свой вариант:", reply_markup=keyboard
        )
        await FSMClient.waiting_for_children.set()

    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное число (например: 1, 2, 3). Попробуйте снова:"
        )
