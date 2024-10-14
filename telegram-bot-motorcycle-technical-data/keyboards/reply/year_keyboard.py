from telebot.types import KeyboardButton, ReplyKeyboardMarkup


def year_buttons() -> ReplyKeyboardMarkup:
    keyboard_year = ReplyKeyboardMarkup(resize_keyboard=True,
                                        one_time_keyboard=True)
    button_yes = KeyboardButton('\U00002705 Да')
    button_no = KeyboardButton('\U0000274C Нет')
    keyboard_year.add(button_yes, button_no)
    return keyboard_year
