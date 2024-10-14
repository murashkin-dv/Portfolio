from telebot.types import BotCommand

from config_data.config import DEFAULT_COMMANDS


def set_default_commands(bot) -> None:
    """
    Defining a Bot default commands list
    :param bot: bot
    :return: None
    """
    bot.set_my_commands([BotCommand(*i) for i in DEFAULT_COMMANDS])