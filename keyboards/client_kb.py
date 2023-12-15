from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

b_info = KeyboardButton('/info')
b_start_path_script = KeyboardButton('Начать')
# b_location = KeyboardButton('/locate', request_location=True)

b_phone = KeyboardButton('Phone', request_contact=True)
# b_location = KeyboardButton('My location', request_location=True)



kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b_info).row(b_start_path_script)
