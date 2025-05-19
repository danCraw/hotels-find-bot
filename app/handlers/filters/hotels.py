from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import dp
from app.handlers.sessions import FSMClient


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.days_of_stay
)
async def process_days_of_stay(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)

        if days <= 0:
            await message.answer(
                "Количество дней должно быть положительным числом. Пожалуйста, введите снова:"
            )
            return

        if days > 100:
            await message.answer("Слишком большое количество дней. Введите снова:")
            return

        if days < 1:
            await message.answer(
                "Минимальный срок проживания - 1 день. Пожалуйста, введите снова:"
            )
            return

        await state.update_data(days_of_stay=days)

        await message.answer(
            "Далее введите время (в часах или минутах), через которое хотите остановиться в "
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
