
from aiogram import Bot, Dispatcher, types, utils, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())