from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_guests_keyboard():
    markup = InlineKeyboardMarkup(row_width=4)
    buttons = [
        InlineKeyboardButton(str(i), callback_data=f"booking:guests:{i}")
        for i in range(1, 5)
    ]
    markup.add(*buttons)
    markup.row(InlineKeyboardButton("Другое", callback_data="booking:guests:custom"))
    return markup


def get_children_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("Нет детей", callback_data="booking:children:0"),
        InlineKeyboardButton("1 ребенок", callback_data="booking:children:1"),
        InlineKeyboardButton("2 ребенка", callback_data="booking:children:2"),
        InlineKeyboardButton("3+ детей", callback_data="booking:children:3"),
    )
    return markup


def get_ages_keyboard():
    markup = InlineKeyboardMarkup(row_width=4)
    ages = [str(i) for i in range(1, 18)]
    buttons = [
        InlineKeyboardButton(age, callback_data=f"booking:age:{age}") for age in ages
    ]
    markup.add(*buttons)
    return markup
