from aiogram import executor
from app.create_bot import dp
from app.handlers import other, common


async def on_startup(_):
    print("The bot has started")


common.handler_register(dp)
other.other_handler_register(dp)

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
