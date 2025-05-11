from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from app.handlers.route_builder import send_travel_time
from app.handlers.sessions import FSMClient
from app.keyboards import kb_client
from app.models.city import City
from app.models.point import Point

FSMClient.next = AsyncMock()
FSMClient.waiting_for_adults = AsyncMock()


@pytest.fixture
def sample_route_data():
    return {
        'steps': [
            {'duration': 60, 'way_points': [0, 1]},
            {'duration': 30, 'way_points': [1, 2]}
        ],
        'coordinates': [
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 2.0)
        ]
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
        'city': City(name="Санкт-Петербург", point=Point(lat=59.93, lon=30.31)),
        'days_of_stay': 2,
        'adults': 2,
        'children_age': [],
        'path_data': sample_route_data
    }
    proxy = AsyncMock()
    proxy.__aenter__.return_value = proxy_data
    proxy.__aexit__.return_value = None
    mock_state.proxy = lambda: proxy
    return mock_state


@pytest.mark.asyncio
@patch("app.handlers.route_builder.find_coordinates_by_time", return_value=Point(lat=55.75, lon=37.62))
@patch("app.handlers.route_builder.find_hotels_by_coordinates")
@patch("app.handlers.route_builder.get_hotel_rooms")
async def test_send_travel_time_found(
        mock_get_rooms, mock_find_hotels, mock_find_point, message, state
):
    mock_hotel = MagicMock()
    mock_hotel.ya_id = "hotel123"
    mock_hotel.name = "Test Hotel"
    mock_hotel.address = "Test Street"
    mock_hotel.url = "http://testhotel.com"
    mock_find_hotels.return_value = [mock_hotel]

    mock_get_rooms.return_value = [{
        'name': 'Стандарт',
        'description': 'Уютный номер',
        'offers': [{
            'price': {'value': 5000},
            'cancellation': {'refund_type': 'FREE'},
            'id': 'offer123'
        }]
    }]

    message.text = "4 часа"
    with patch("app.create_bot.bot.send_message") as mock_send:
        await send_travel_time(message, state)

    message.reply.assert_called_with("Гостиницы, которые я нашел", reply_markup=kb_client)
    assert state.proxy().__aenter__.return_value.get('confirmed_hotels') is not None


@pytest.mark.asyncio
async def test_send_travel_time_invalid_format(message, state):
    message.text = "непонятное время"
    with patch("app.create_bot.bot.send_message"):
        await send_travel_time(message, state)
    message.reply.assert_called_with('Пожалуйста, введите данные в верном формате...')


@pytest.mark.asyncio
@patch("app.handlers.route_builder.find_coordinates_by_time", return_value=Point(lat=55.75, lon=37.62))
@patch("app.handlers.route_builder.find_hotels_by_coordinates", return_value=[])
async def test_send_travel_time_not_found(mock_hotels, mock_point, message, state):
    message.text = "3 часа"
    with patch("app.create_bot.bot.send_message"):
        await send_travel_time(message, state)
    message.reply.assert_called_with("К сожалению, не удалось найти подходящие отели.")
