from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import dp
from app.handlers.sessions import FSMClient


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.waiting_for_children
)
async def process_children_input(message: types.Message, state: FSMContext):
    try:
        children = int(message.text)
        if children < 0:
            await message.answer(
                "Количество детей не может быть отрицательным. Пожалуйста, введите снова:"
            )
            return
        if children > 10:
            await message.answer(
                "Слишком большое количество детей. Максимум 10. Введите снова:"
            )
            return

        await state.update_data(children=children)

        if children > 0:
            await message.answer(
                f"Введите возраст для каждого из {children} детей через запятую (например: 5, 8):"
            )
            await FSMClient.waiting_for_children_age.set()
        else:
            await message.answer("Сколько дней вы планируете провести в отеле?")
            await FSMClient.days_of_stay.set()

    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное число детей (например: 0, 1, 2). Попробуйте снова:"
        )


@dp.message_handler(
    lambda msg: not msg.text.startswith("/"), state=FSMClient.waiting_for_children_age
)
async def process_children_age_input(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        children_count = user_data.get("children", 0)

        ages = [age.strip() for age in message.text.split(",")]

        if len(ages) != children_count:
            await message.answer(
                f"Вы указали {len(ages)} возрастов, но детей {children_count}. Пожалуйста, введите ровно {children_count} возраста через запятую:"
            )
            return

        valid_ages = []
        for age in ages:
            try:
                age_int = int(age)
                if age_int <= 0:
                    await message.answer(
                        f"Возраст '{age}' недопустим. Возраст должен быть положительным числом. Введите возрасты снова:"
                    )
                    return
                if age_int > 17:
                    await message.answer(
                        f"Возраст '{age}' слишком большой для ребенка. Максимальный возраст ребенка - 17 лет. Введите возрасты снова:"
                    )
                    return
                valid_ages.append(age_int)
            except ValueError:
                await message.answer(
                    f"Некорректный возраст '{age}'. Пожалуйста, введите только числа через запятую (например: 5, 8):"
                )
                return

        await state.update_data(children_age=valid_ages)
        await message.answer("Сколько дней вы планируете провести в отеле?")
        await FSMClient.days_of_stay.set()

    except Exception:
        await message.answer(
            "Произошла ошибка при обработке возрастов. Пожалуйста, введите возрасты детей через запятую еще раз:"
        )
