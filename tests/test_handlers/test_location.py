import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, Location
from aiogram.dispatcher import FSMContext

from app.handlers.location import user_loc, handle_location, send_city
from app.handlers.sessions import FSMClient
from app.models.point import Point
from app.models.city import City


FSMClient.next = AsyncMock()
FSMClient.target_city = AsyncMock()


@pytest.fixture
def message():
    msg = AsyncMock(spec=Message)
    msg.from_user.id = 1111
    msg.chat.id = 1111
    return msg


@pytest.fixture
def state():
    mock_state = AsyncMock(spec=FSMContext)
    proxy_data = {}
    proxy = AsyncMock()
    proxy.__aenter__.return_value = proxy_data
    proxy.__aexit__.return_value = None
    mock_state.proxy = lambda: proxy
    return mock_state


@pytest.mark.asyncio
@patch("app.handlers.location.location_kb", return_value="mock_kb")
async def test_user_loc(mock_kb, message):
    message.text = "/start"
    await user_loc(message)
    message.answer.assert_called_with(
        "Пожалуйста, введите город отправления "
        'или поделитесь своей геопозицией, нажав на кнопку "📍 Отправить местоположение". '
        'Чтобы выйти, нажмите или нажмите "Отмена" ',
        reply_markup="mock_kb",
    )


@pytest.mark.asyncio
@patch(
    "app.handlers.location.openrouteservice_reverse_geocoding",
    return_value="Санкт-Петербург",
)
async def test_handle_location(mock_reverse_geo, message, state):
    message.location = Location(latitude=59.93, longitude=30.31)
    await handle_location(message, state)

    data = await state.proxy().__aenter__()
    assert isinstance(data["city"], City)
    assert data["city"].name == "Санкт-Петербург"
    assert data["city"].point.lat == 59.93
    assert data["city"].point.lon == 30.31

    message.answer.assert_any_call("📍 Место отправления сохранено!")


@pytest.mark.asyncio
@patch(
    "app.handlers.location.openrouteservice_city_geocoding",
    return_value=Point(lat=55.75, lon=37.62),
)
async def test_send_city(mock_geocode, message, state):
    message.text = "Москва"
    await send_city(message, state)

    data = await state.proxy().__aenter__()
    assert isinstance(data["city"], City)
    assert data["city"].name == "Москва"
    assert data["city"].point.lat == 55.75
    assert data["city"].point.lon == 37.62

    message.answer.assert_called_with("Введите город, в который Вы едете")
