from loader import bot
import handlers
from telebot.custom_filters import IsDigitFilter, StateFilter
from utils.set_bot_commands import set_default_commands

import os

from peewee import SqliteDatabase
from database import database
from loguru import logger


@logger.catch
def create_database() -> None:
    work_directory = os.path.abspath(os.getcwd())
    db_abspath = os.path.join(work_directory, "database", "participants.db")
    if os.path.isfile(db_abspath):
        print("A database exists already and it will continue logging.")
    else:
        print("New database has been created successfully.")

    db = SqliteDatabase(db_abspath)
    database.proxy.initialize(db)
    db.create_tables([database.UserData, database.UserMessageLog])


if __name__ == "__main__":
    create_database()
    bot.add_custom_filter(StateFilter(bot))
    bot.add_custom_filter(IsDigitFilter())
    set_default_commands(bot)
    bot.infinity_polling()
