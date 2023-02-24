from aiogram import types, Dispatcher
from create_bot import bot, dp
from keyboards import kb_client

# @dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id, 'Hello', reply_markup=kb_client)

# @dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    await message.answer("Some info")


# @dp.message_handler(commands=['location'])
async def get_location(message: types.Message):
    await bot.send_message(message.from_user.id, 'location')


def client_handler_register(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'])
    dp.register_message_handler(get_info, commands=['info'])
    dp.register_message_handler(get_location, commands='location')
