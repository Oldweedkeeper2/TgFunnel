import os
from datetime import timedelta

from environs import Env

env = Env()
env.read_env()

TRIGGER_WORDS = ["прекрасно", "ожидать"]
MESSAGES = [  # DEBUG, переделать на 6 минут, 39 минут и 1 день 2 часа для прода
    {"index": 1, "delay": timedelta(seconds=6), "text": "Текст1"},
    {"index": 2, "delay": timedelta(seconds=8), "text": "Текст2"},
    {"index": 3, "delay": timedelta(seconds=12), "text": "Текст3"}
]

DATABASE_URL: str = env.str("DATABASE_URL", "postgresql+asyncpg://login:password@localhost/dbname")
LOG_DIR: str = env.str("LOG_DIR", "./logs")

API_ID = env.int("API_ID", None)
API_HASH = env.str("API_HASH", None)
API_NAME = env.str("API_NAME", "my_account")

if API_ID is None or API_HASH is None or API_NAME is None:  # noqa
    raise Exception("API_ID, API_HASH и API_NAME не могут быть пустыми!")

os.makedirs(LOG_DIR, exist_ok=True)
