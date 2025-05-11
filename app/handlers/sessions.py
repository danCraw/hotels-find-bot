from aiogram.dispatcher.filters.state import State, StatesGroup


class FSMClient(StatesGroup):
    point = State()
    target_city = State()
    waiting_for_adults = State()
    travel_time = State()
    verifying_codes = State()
    waiting_for_children = State()
    waiting_for_children_age = State()
    days_of_stay = State()
    client_info = State()
    booking_data = State()
