from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2


from app.config import BOT_TOKEN, REDIS_PASSWORD, REDIS_DB, REDIS_PORT, REDIS_HOST

redis_storage = RedisStorage2(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    prefix="fsm_bot",
    state_ttl=60 * 10,
)


bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot, storage=redis_storage)
