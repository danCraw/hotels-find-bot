import json
from aiogram import types, Dispatcher
from create_bot import bot, dp
from aiogram.types import KeyboardButton
from keyboards import kb_client
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram.utils.markdown as md


@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id,
                           'Привет, я бот для поиска отелей в дороге. Как я работаю: спрашиваю у Вас текущее местоположение, '
                           'потом город, в который едете, затем Вы можете указать время, через которое хотели бы сделать '
                           'остановку в отеле, я составлю маршрут и рассчитаю примерное место, в котором Вы окажетесь.',
                           reply_markup=kb_client)


''' INFO'''


@dp.message_handler(commands=['info'])
async def get_info(message: types.Message):
    await bot.send_message(message.from_user.id, "some info")


'''USER LOCATION'''


class FSMClient(StatesGroup):
    point = State()
    destination_city = State()
    travel_time = State()



@dp.message_handler(commands=['go'], state=None)
async def user_loc(message: types.Message):
    # if LAT is None or LON is None:
    #     await bot.send_message(message.from_user.id,
    #                            'Пожалуйста, введите свое местоположение, нажав на кнопку My location')
    #     return
    await FSMClient.point.set()
    b_location = KeyboardButton('/locate', request_location=True)
    kb_client.add(b_location)
    await message.answer('Пожалуйста, введите город отправления '
                         'или поделитесь своей геопозицией, нажав на кнопку  "locate", чтобы ', reply_markup=kb_client)

@dp.message_handler(state='*', commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cansel_handler(message: types.Message, state: FSMContext):
    cur_state = await state.get_state()
    if cur_state is None:
        return
    await state.finish()
    await message.reply('отмена')

@dp.message_handler(state=FSMClient.point)
async def send_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['point'] = message.text
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')

@dp.message_handler(state=FSMClient.point, content_types=['location'])
async def user_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"latitude:{lat}\nlongitude:{lon}"
    async with state.proxy() as data:
        data['point'] = {'lat': lat, 'lon': lon}
    await FSMClient.next()
    await message.answer('Введите город, в который Вы едете')
    # await bot.send_message(message.from_user.id, coordinates)

@dp.message_handler(state=FSMClient.destination_city)
async def send_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['destination_city'] = message.text
    await FSMClient.next()
    await message.reply('Далее введите время (в часах или минутах), через которое хотите остановиться в '
                        'отеле.Например: "3 часа" или "56 минут"')


@dp.message_handler(state=FSMClient.travel_time)
async def send_travel_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['travel_time'] = message.text

    async with state.proxy() as data:
        await bot.send_message(
            message.from_user.id,
            md.text(
                md.text(data['point']),
                md.text(data['destination_city']),
                md.text(data['travel_time']),
                sep='\n',
            ),
        )
    await state.finish()




# @dp.message_handler(content_types=['location'])
# async def user_location(message: types.Message):
#     lat = message.location.latitude
#     lon = message.location.longitude
#     coordinates = f"latitude:{lat}\nlongitude:{lon}"
#     await bot.send_message(message.from_user.id, coordinates)


def client_handler_register(dp: Dispatcher):
    pass
    # dp.register_message_handler(start_command, commands=['start', 'help'])
    # dp.register_message_handler(get_info, commands=['info'])
    # dp.register_message_handler(user_location, content_types=['location'])
