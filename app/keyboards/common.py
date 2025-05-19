from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def cancel_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена"))


def location_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("📍 Отправить местоположение", request_location=True),
        KeyboardButton("Отмена"),
    )
