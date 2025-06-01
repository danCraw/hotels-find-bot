import aiogram.utils.markdown as md
from aiogram import types
from aiogram.dispatcher import FSMContext

from app.create_bot import bot, dp
from app.handlers.sessions import FSMClient
from app.keyboards import kb_client
from app.keyboards.common import location_kb


@dp.message_handler(commands=["start", "help"])
async def start_command(message: types.Message):
    """Send welcome message to user"""
    await bot.send_message(
        message.from_user.id,
        "Привет, я бот для поиска отелей в дороге. Как я работаю: спрашиваю у Вас текущее местоположение, "
        "потом город, в который едете, затем Вы можете указать время, через которое хотели бы сделать "
        "остановку в отеле, я составлю маршрут и рассчитаю примерное место, в котором Вы окажетесь.",
        reply_markup=kb_client,
    )


@dp.message_handler(commands=["info"])
async def get_info(message: types.Message):
    """Send info about bot"""
    await bot.send_message(
        message.from_user.id,
        md.text(
            md.text("Всё, что Вам нужно указать, чтобы я нашел лучшие отели для Вас:"),
            md.text(
                "* ввести город отправления или указать свою локацию (доступно с мобильного устройства)"
            ),
            md.text("* далее необходимо ввести город назначения"),
            md.text(
                "* и затем ввести время, через которое хотите остановиться в отеле"
            ),
            sep="\n",
        ),
    )


@dp.message_handler(commands=["newsearch"], state="*", content_types=["text"])
async def new_search(message: types.Message, state: FSMContext):
    """Start a new hotel search by resetting the state"""
    await state.finish()
    await FSMClient.next()
    await bot.send_message(
        message.from_user.id,
        "Отлично! Начнём новый поиск отеля. Укажите своё местоположение или город отправления.",
        reply_markup=location_kb(),
    )


@dp.message_handler(commands=["back"], state="*")
async def go_back(message: types.Message, state: FSMContext):
    """Go back one step in FSM state machine"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Вы сейчас не в процессе диалога.")
        return

    try:
        prev_state = await FSMClient.previous()
    except ValueError:
        await message.answer("Невозможно определить текущее состояние.")
        return

    await state.set_state(prev_state)

    await message.answer("Возвращаемся назад")
