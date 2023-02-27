
from aiogram import Bot, Dispatcher, types, utils, executor


TOKEN = None

with open("context/token.txt") as f:
    TOKEN = f.read().strip()

bot = Bot(TOKEN)
dp = Dispatcher(bot)