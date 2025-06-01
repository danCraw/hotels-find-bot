from aiogram import Dispatcher

from app.handlers.filters.adults import process_adults_input  # noqa
from app.handlers.filters.childrens import (  # noqa
    process_children_input,
    process_children_age_input,
)
from app.handlers.filters.hotels import process_days_of_stay  # noqa
from app.handlers.location import handle_location
from app.handlers.start import start_command, get_info, new_search, go_back
from app.handlers.route_builder import send_route_data, send_travel_time  # noqa


def handler_register(dp: Dispatcher):
    dp.register_message_handler(new_search, commands=["newsearch"], state="*")
    dp.register_message_handler(go_back, commands=["back"], state="*")
    dp.register_message_handler(start_command, commands=["start", "help"], state=None)
    dp.register_message_handler(get_info, commands=["info"], state="*")
    dp.register_message_handler(handle_location, content_types=["location"], state="*")
