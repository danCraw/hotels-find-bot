import time

import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from app.handlers import verifications


@pytest.fixture
def message():
    msg = AsyncMock(spec=Message)
    msg.text = "Email: 123456\nТелефон: 654321"
    return msg


@pytest.fixture
def fsm_data():
    return {
        "booking_email_code": "123456",
        "booking_phone_code": "654321",
        "email": "test@example.com",
        "phone": "+79991234567",
        "codes_expire": int(time.time()) + 100,
        "attempts_left": 3,
        "offer_id": "123",
    }


@pytest.fixture
def state(fsm_data):
    mock_state = AsyncMock(spec=FSMContext)
    proxy = AsyncMock()
    proxy.__aenter__.return_value = fsm_data
    proxy.__aexit__.return_value = None
    mock_state.proxy = lambda: proxy
    return mock_state


@pytest.mark.asyncio
@patch("app.handlers.verifications.create_payment_link", new_callable=AsyncMock)
async def test_verify_codes_success(mock_create_payment_link, message, state, fsm_data):
    await verifications.verify_codes(message, state)
    message.answer.assert_any_call("✅ Коды подтверждены! Переходим к созданию заказа ")
    mock_create_payment_link.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_codes_expired(message, state, fsm_data):
    fsm_data["codes_expire"] = int(time.time()) - 1
    await verifications.verify_codes(message, state)
    message.answer.assert_called_with(
        "⌛ Время действия кодов истекло. Запросите новые."
    )


@pytest.mark.asyncio
@patch("app.handlers.verifications.create_payment_link", new_callable=AsyncMock)
async def test_verify_codes_wrong_codes(message, state, fsm_data):
    message.text = "Email: 111111\nТелефон: 654321"
    await verifications.verify_codes(message, state)
    assert "Неверные коды" in message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("app.handlers.verifications.create_payment_link", new_callable=AsyncMock)
async def test_verify_codes_wrong_format(message, state, fsm_data):
    message.text = "123456 654321"
    await verifications.verify_codes(message, state)
    message.answer.assert_any_call(
        "❌ Неправильный формат. Используйте:\nEmail: 123456\nТелефон: 654321"
    )


@pytest.mark.asyncio
@patch("app.handlers.verifications.send_email_code", new_callable=AsyncMock)
@patch("app.handlers.verifications.send_sms_code", new_callable=AsyncMock)
async def test_resend_codes_success(mock_sms, mock_email, message, state, fsm_data):
    fsm_data["last_resend_time"] = int(time.time()) - 40
    await verifications.resend_verification_codes(message, state)
    message.answer.assert_called_with(
        "✅ Новые коды отправлены! Проверьте почту и SMS."
    )
    assert "booking_email_code" in fsm_data
    assert "booking_phone_code" in fsm_data
    assert "codes_expire" in fsm_data


@pytest.mark.asyncio
async def test_resend_codes_too_soon(message, state, fsm_data):
    fsm_data["last_resend_time"] = int(time.time())
    await verifications.resend_verification_codes(message, state)
    assert "⏳ Повторная отправка будет доступна" in message.answer.call_args[0][0]
