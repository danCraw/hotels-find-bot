from aiogram import types, Dispatcher
from create_bot import dp


# @dp.message_handler()
async def echo_send(message: types.Message):
    await message.answer('error')


def other_handler_register(dp: Dispatcher):
    dp.register_message_handler(echo_send)