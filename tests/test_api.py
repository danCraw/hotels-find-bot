import pytest
from calculations import find_rooms_by_params


@pytest.mark.asyncio
async def test_find_rooms_by_params():
    hot_name = 'otel_izmailovo_gamma'
    adults = 2
    childrens = 0
    rooms = await find_rooms_by_params(hot_name, adults, childrens)

    print(rooms)