import json

from loguru import logger
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message)

from loader import bot


@logger.catch
def message_by_page(message: Message,
                    page: int = 1,
                    current_user_id: int = 0) -> None:
    """
    Function uses pagination for long messages. It keeps search result
    as incoming data and passes it to internal function for further pagination
    It sends only 1 (first page)
    :param message: Message
    :param page: int
    :param current_user_id: int
    :return: None
    """

    with bot.retrieve_data(current_user_id) as data:
        page_total = len(data['pages'])
        page_data = data['pages'][page - 1]

    page_text = json.dumps(page_data, indent=2)

    left = page - 1 if page != 1 else page_total
    right = page + 1 if page != page_total else 1

    keyboard_pages = InlineKeyboardMarkup()
    left_button = InlineKeyboardButton('←',
                                       callback_data=f'to {left}')
    page_button = InlineKeyboardButton(f'{str(page)}/{str(page_total)}',
                                       callback_data='_')
    right_button = InlineKeyboardButton('→',
                                        callback_data=f'to {right}')
    exit_button = InlineKeyboardButton('Exit', callback_data='exit')
    keyboard_pages.add(left_button, page_button, right_button)
    keyboard_pages.add(exit_button)

    if message.reply_markup:
        bot.edit_message_text(page_text,
                              message.chat.id,
                              message.message_id,
                              reply_markup=keyboard_pages)
    else:
        bot.send_message(message.chat.id,
                         page_text,
                         reply_markup=keyboard_pages)

        bot.send_message(message.chat.id,
                         'Вы можете продолжить текущий поиск, введя новое '
                         'название Брэнда (Модели).\n'
                         'Для выхода из текущего режима поиска - нажмите '
                         'кнопку Exit\n'
                         'или введите команду /cancel')


@bot.callback_query_handler(func=lambda call: True)
def callback(call) -> None:
    """
    Function handles button pressing in messages with pages.
    :param call: str
    :return: none
    """

    if 'to' in call.data:
        new_page = int(call.data.split(' ')[1])
        message_by_page(message=call.message,
                        page=new_page,
                        current_user_id=call.from_user.id)
    elif 'exit' in call.data:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.from_user.id,
                         'Введите новую команду.\n'
                         'Используйте команду /help для справки\n'
                         'или встроенное меню выбора команд')
