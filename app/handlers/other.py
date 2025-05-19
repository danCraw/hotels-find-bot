from aiogram import types, Dispatcher


# @dp.message_handler()
async def echo_send(message: types.Message):
    await message.answer("error")


def other_handler_register(dp: Dispatcher):
    dp.register_message_handler(echo_send)
