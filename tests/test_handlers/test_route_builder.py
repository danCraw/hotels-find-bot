from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from app.handlers.route_builder import send_travel_time, show_hotels_batch
from app.handlers.sessions import FSMClient
from app.models.city import City
from app.models.point import Point

FSMClient.next = AsyncMock()
FSMClient.waiting_for_adults = AsyncMock()


@pytest.fixture
def sample_route_data():
    return {
        "steps": [
            {"duration": 60, "way_points": [0, 1]},
            {"duration": 30, "way_points": [1, 2]},
        ],
        "coordinates": [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
    }


@pytest.fixture
def message():
    msg = AsyncMock(spec=Message)
    msg.text = "Москва"
    msg.from_user.id = 12345
    msg.date = datetime.now()
    return msg


@pytest.fixture
def state(sample_route_data):
    mock_state = AsyncMock(spec=FSMContext)
    proxy_data = {
        "city": City(name="Санкт-Петербург", point=Point(lat=59.93, lon=30.31)),
        "days_of_stay": 2,
        "adults": 2,
        "children_age": [],
        "path_data": sample_route_data,
    }
    proxy = AsyncMock()
    proxy.__aenter__.return_value = proxy_data
    proxy.__aexit__.return_value = None
    mock_state.proxy = lambda: proxy
    return mock_state


@pytest.mark.asyncio
async def test_send_travel_time_invalid_format(message, state):
    message.text = "непонятное время"
    with patch("app.create_bot.bot.send_message"):
        await send_travel_time(message, state)
    message.reply.assert_called_with("Пожалуйста, введите данные в верном формате...")


@pytest.mark.asyncio
async def test_show_hotels_batch_shows_hotels(message):
    data = {
        "current_hotel_index": 0,
        "all_hotels": [
            MagicMock(name="Hotel A", stars=3, avg_price=1000, rooms=[{}], url="", address="Address A", ostrovok_id="1"),
            MagicMock(name="Hotel B", stars=4, avg_price=1500, rooms=[{}], url="", address="Address B", ostrovok_id="2"),
        ],
    }

    await show_hotels_batch(message, data, batch_size=1)

    assert message.answer.call_count >= 2
