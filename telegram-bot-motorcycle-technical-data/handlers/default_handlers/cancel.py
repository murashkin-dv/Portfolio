from telebot.types import Message, ReplyKeyboardRemove

from database.database import DataBaseCRUD
from loader import bot


@bot.message_handler(commands=["cancel"])
def cancel_state(message: Message) -> None:
    """
    Function cancels any command for the current User.
    :param message: incoming message from a user
    :return: none
    """
    bot.send_message(message.from_user.id,
                     f"Команда отменена. Введите новую команду или "
                     f"воспользуйтесь помощью c /help",
                     reply_markup=ReplyKeyboardRemove())
    bot.delete_state(message.from_user.id, message.chat.id)

    # history log update
    DataBaseCRUD.log_message(message.from_user.id, message.text)
