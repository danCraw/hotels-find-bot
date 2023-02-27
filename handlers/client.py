from aiogram import types, Dispatcher
from create_bot import bot, dp
from keyboards import kb_client

# @dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id, 'Hello', reply_markup=kb_client)

''' INFO'''
# @dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    await message.answer("Some info")


'''MY LOCATION'''

# def get_keyboard():
#     keyboard = types.ReplyKeyboardMarkup()
#     button = types.KeyboardButton("Share Position", request_location=True)
#     keyboard.add(button)
#     return keyboard
# @dp.message_handler(content_types=['location'])

# @dp.message_handler(content_types=['location'])
async def my_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"latitude:{lat}\nlongitude:{lon}"
    await message.answer(coordinates)


def client_handler_register(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'])
    dp.register_message_handler(get_info, commands=['info'])
    dp.register_message_handler(my_location, content_types=['location'])
