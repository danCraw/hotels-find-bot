from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('/info')
b2 = KeyboardButton('/location')

b_phone = KeyboardButton('Phone', request_contact=True)
b_location = KeyboardButton('Location', request_location=True)

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b1).add(b2).row(b_phone, b_location)