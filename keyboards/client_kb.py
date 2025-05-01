from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

b_info = KeyboardButton('/info')
b_start_path_script = KeyboardButton('Начать')
# b_location = KeyboardButton('/locate', request_location=True)

b_phone = KeyboardButton('Phone', request_contact=True)
# b_location = KeyboardButton('My location', request_location=True)



kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b_info).row(b_start_path_script)


def filters_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton("1 взрослый", callback_data='adults_1'))
    keyboard.add(InlineKeyboardButton("2 взрослых", callback_data='adults_2'))
    keyboard.add(InlineKeyboardButton("3 взрослых", callback_data='adults_3'))

    keyboard.add(InlineKeyboardButton("1 ребенок", callback_data='children_1'))
    keyboard.add(InlineKeyboardButton("2 ребенка", callback_data='children_2'))

    keyboard.add(InlineKeyboardButton("С питомцами", callback_data='pets_yes'))
    keyboard.add(InlineKeyboardButton("Без питомцев", callback_data='pets_no'))

    return keyboard