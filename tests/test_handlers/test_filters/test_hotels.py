import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message

from app.handlers.filters.hotels import process_days_of_stay
from app.handlers.sessions import FSMClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text, expected_reply, should_pass",
    [
        ("abc", "Пожалуйста, введите корректное количество дней", False),
        ("0", "Количество дней должно быть положительным числом", False),
        ("-5", "Количество дней должно быть положительным числом", False),
        ("101", "Слишком большое количество дней", False),
        ("1", "Далее введите время", True),
        ("7", "Далее введите время", True),
    ],
)
async def test_process_days_of_stay(input_text, expected_reply, should_pass):
    message = AsyncMock(spec=Message)
    message.text = input_text
    message.answer = AsyncMock()

    state = AsyncMock()
    state.update_data = AsyncMock()

    FSMClient.travel_time.set = AsyncMock()

    await process_days_of_stay(message, state)

    message.answer.assert_called()
    args, _ = message.answer.call_args
    assert expected_reply in args[0]

    if should_pass:
        state.update_data.assert_called_once_with(days_of_stay=int(input_text))
        FSMClient.travel_time.set.assert_called_once()
    else:
        state.update_data.assert_not_called()
