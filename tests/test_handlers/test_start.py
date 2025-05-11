import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message

from app.handlers.start import start_command, get_info


@pytest.mark.asyncio
async def test_start_command():
    message = AsyncMock(spec=Message)
    message.from_user.id = 123

    with patch("app.create_bot.bot.send_message") as mock_send:
        await start_command(message)

        mock_send.assert_awaited_once()
        args, kwargs = mock_send.call_args

        assert args[0] == 123  # user_id
        assert "Привет, я бот для поиска отелей" in args[1]  # message text
        assert "Как я работаю" in args[1]
        assert "местоположение" in args[1]
        assert "город" in args[1]
        assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_get_info():
    message = AsyncMock(spec=Message)
    message.from_user.id = 456

    with patch("app.create_bot.bot.send_message") as mock_send:
        await get_info(message)

        mock_send.assert_awaited_once()
        args, kwargs = mock_send.call_args

        assert args[0] == 456  # user_id
        assert "отели" in args[1] or "нуж" in args[1]  # часть описания
        assert "* ввести город отправления" in args[1]
        assert "* далее необходимо ввести город" in args[1]
        assert "* и затем ввести время" in args[1]
