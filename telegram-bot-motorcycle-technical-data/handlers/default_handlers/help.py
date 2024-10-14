from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS

from database.database import DataBaseCRUD
from loader import bot


@bot.message_handler(commands=["help"])
def bot_help(message: Message) -> None:
    """
    This handler sends a message with a Help information
    :param message: incoming message from a user
    :return: none
    """
    text = [f"/{command} - {description}" for command, description in
            DEFAULT_COMMANDS]
    bot.reply_to(message, "\n".join(text))

    # history log update
    DataBaseCRUD.log_message(message.from_user.id, message.text)
