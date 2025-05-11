import aiogram.utils.markdown as md
from aiogram import types

from app.create_bot import bot, dp
from app.keyboards import kb_client


@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    """Send welcome message to user"""
    await bot.send_message(message.from_user.id,
                           'Привет, я бот для поиска отелей в дороге. Как я работаю: спрашиваю у Вас текущее местоположение, '
                           'потом город, в который едете, затем Вы можете указать время, через которое хотели бы сделать '
                           'остановку в отеле, я составлю маршрут и рассчитаю примерное место, в котором Вы окажетесь.',
                           reply_markup=kb_client)


@dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    """Send info about bot"""
    await bot.send_message(message.from_user.id, md.text(
        md.text("Всё, что Вам нужно указать, чтобы я нашел лучшие отели для Вас:"),
        md.text("* ввести город отправления или указать свою локацию (доступно с мобильного устройства)"),
        md.text("* далее необходимо ввести город назначения"),
        md.text("* и затем ввести время, через которое хотите остановиться в отеле"),
        sep='\n',
    ))
