import os

from dotenv import find_dotenv, load_dotenv


if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

RAPID_API_HOST = "motorcycles-by-api-ninjas.p.rapidapi.com"
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("brand", "Поиск по брэнду"),
    ("model", "Поиск по модели"),
    ("history", "История запросов"),
    ("cancel", "Отменить команду"),
    ("help", "Вывести справку")
)
