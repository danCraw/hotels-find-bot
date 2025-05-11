import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from datetime import datetime

from app.handlers.client_info import process_client_info
from app.handlers.sessions import FSMClient

FSMClient.verifying_codes = AsyncMock()


@pytest.fixture
def message():
    msg = AsyncMock(spec=Message)
    msg.from_user.id = 123
    msg.date = datetime.now()
    return msg


@pytest.fixture
def state():
    mock_state = AsyncMock(spec=FSMContext)
    data = {}
    proxy = AsyncMock()
    proxy.__aenter__.return_value = data
    proxy.__aexit__.return_value = None
    mock_state.proxy = lambda: proxy
    return mock_state


@pytest.mark.asyncio
@patch("app.handlers.client_info.send_email_code", new_callable=AsyncMock)
@patch("app.handlers.client_info.send_sms_code", new_callable=AsyncMock)
async def test_process_client_info_success(mock_sms, mock_email, message, state):
    message.text = (
        "Телефон: +79123456789\n"
        "Email: test@example.com\n"
        "1. Иван Иванов\n"
        "2. Мария Иванова"
    )

    await process_client_info(message, state)

    mock_email.assert_called_once()
    mock_sms.assert_called_once()
    message.answer.assert_any_call(
        "📬 Коды подтверждения отправлены на ваш email и телефон.\n\n"
        "Введите коды в формате:\n"
        "Email: 123456\n"
        "Телефон: 654321",
        reply_markup=message.answer.call_args_list[-1][1]["reply_markup"]
    )


@pytest.mark.asyncio
async def test_process_client_info_invalid_phone(message, state):
    message.text = (
        "Телефон: 12345\n"
        "Email: test@example.com\n"
        "1. Иван Иванов"
    )

    await process_client_info(message, state)
    message.answer.assert_called_with("❌ Неверный формат телефона")


@pytest.mark.asyncio
async def test_process_client_info_invalid_email(message, state):
    message.text = (
        "Телефон: +79123456789\n"
        "Email: wrong_email\n"
        "1. Иван Иванов"
    )

    await process_client_info(message, state)
    message.answer.assert_called_with("❌ Неверный формат email")


@pytest.mark.asyncio
async def test_process_client_info_missing_fields(message, state):
    message.text = "Просто текст без нужных данных"

    await process_client_info(message, state)
    message.answer.assert_any_call("Некорректный формат данных. Пожалуйста, введите данные в формате:\n\n"
                                   "номер телефона: +79123456789\n"
                                   "e-mail: example@mail.com\n"
                                   "1. Иван Иванов\n"
                                   "2. Мария Иванова\n"
                                   "3. Пётр Иванов ребёнок 5 лет")


@pytest.mark.asyncio
@patch("app.handlers.client_info.send_email_code", new_callable=AsyncMock, side_effect=Exception("fail"))
@patch("app.handlers.client_info.send_sms_code", new_callable=AsyncMock)
async def test_process_client_info_send_error(mock_sms, mock_email, message, state):
    message.text = (
        "Телефон: +79123456789\n"
        "Email: test@example.com\n"
        "1. Иван Иванов"
    )

    await process_client_info(message, state)

    message.answer.assert_any_call("❌ Ошибка отправки кодов. Проверьте правильность данных и попробуйте снова.")
