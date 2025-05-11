import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, ReplyKeyboardMarkup

from app.handlers.filters.adults import process_adults_input
from app.handlers.sessions import FSMClient

import types
FSMClient.waiting_for_children = types.SimpleNamespace(set=AsyncMock())

@pytest.mark.asyncio
@pytest.mark.parametrize("text, expected_reply, should_set_state", [
    ("0", "Количество взрослых должно быть положительным числом. Пожалуйста, введите снова:", False),
    ("21", "Слишком большое количество взрослых. Максимум 20. Введите снова:", False),
    ("abc", "Пожалуйста, введите корректное число (например: 1, 2, 3). Попробуйте снова:", False),
    ("2", "Выберите количество детей или введите свой вариант:", True),
])
async def test_process_adults_input(text, expected_reply, should_set_state):
    message = AsyncMock(spec=Message)
    message.text = text
    message.answer = AsyncMock()

    state = AsyncMock()
    state.update_data = AsyncMock()

    await process_adults_input(message, state)

    message.answer.assert_called()
    args, kwargs = message.answer.call_args
    assert expected_reply in args[0]

    if text.isdigit() and 0 < int(text) <= 20:
        state.update_data.assert_called_once_with(adults=int(text))
        if should_set_state:
            FSMClient.waiting_for_children.set.assert_called_once()
    else:
        state.update_data.assert_not_called()
