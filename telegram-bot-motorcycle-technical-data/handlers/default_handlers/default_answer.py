from telebot.types import Message

from database.database import DataBaseCRUD
from loader import bot


@bot.message_handler(state=None)
def default_answer(message: Message) -> None:
    """
    A default handler to reply a user which send an unknown
    command or text.

    :param message: Message, incoming message from a user
    :return: none
    """
    bot.send_message(message.chat.id, "Не понимаю Вас: \"" + message.text +
                     "\".\nПопробуйте получить помощь, введя команду /help")

    # history log update
    DataBaseCRUD.log_message(message.from_user.id, message.text)
