from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('/info')
# b2 = KeyboardButton('/locate')

b_phone = KeyboardButton('Phone', request_contact=True)
b_location = KeyboardButton('My location', request_location=True)



kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b1).row(b_phone, b_location)