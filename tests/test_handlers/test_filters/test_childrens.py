import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message

from app.handlers.filters.childrens import (
    process_children_input,
    process_children_age_input,
)
from app.handlers.sessions import FSMClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected_reply, expected_next_state",
    [
        ("-1", "Количество детей не может быть отрицательным", None),
        ("11", "Слишком большое количество детей", None),
        ("abc", "Пожалуйста, введите корректное число детей", None),
        ("0", "Сколько дней вы планируете провести в отеле?", FSMClient.days_of_stay),
        (
            "2",
            "Введите возраст для каждого из 2 детей через запятую",
            FSMClient.waiting_for_children_age,
        ),
    ],
)
async def test_process_children_input(text, expected_reply, expected_next_state):
    message = AsyncMock(spec=Message)
    message.text = text
    message.answer = AsyncMock()

    state = AsyncMock()
    state.update_data = AsyncMock()

    # мок set
    FSMClient.waiting_for_children_age.set = AsyncMock()
    FSMClient.days_of_stay.set = AsyncMock()

    await process_children_input(message, state)

    message.answer.assert_called()
    args, kwargs = message.answer.call_args
    assert expected_reply in args[0]

    if text.isdigit() and 0 <= int(text) <= 10:
        state.update_data.assert_called_once_with(children=int(text))
        if int(text) == 0:
            FSMClient.days_of_stay.set.assert_called_once()
        else:
            FSMClient.waiting_for_children_age.set.assert_called_once()
    else:
        state.update_data.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "children, input_text, expected_reply, should_pass",
    [
        (2, "5, 7", "Сколько дней вы планируете провести в отеле?", True),
        (2, "5", "Вы указали 1 возрастов, но детей 2", False),
        (1, "-1", "Возраст '-1' недопустим", False),
        (1, "abc", "Некорректный возраст 'abc'", False),
        (1, "18", "Возраст '18' слишком большой", False),
    ],
)
async def test_process_children_age_input(
    children, input_text, expected_reply, should_pass
):
    message = AsyncMock(spec=Message)
    message.text = input_text
    message.answer = AsyncMock()

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"children": children})
    state.update_data = AsyncMock()

    FSMClient.days_of_stay.set = AsyncMock()

    await process_children_age_input(message, state)

    message.answer.assert_called()
    args, _ = message.answer.call_args
    assert expected_reply in args[0]

    if should_pass:
        state.update_data.assert_called_once_with(
            children_age=[int(age) for age in input_text.split(",")]
        )
        FSMClient.days_of_stay.set.assert_called_once()
    else:
        state.update_data.assert_not_called()
