import os
from typing import Any, List

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class CustomBot(Bot):
    def __init__(self, token: str, **kwargs: Any) -> None:
        super().__init__(token, **kwargs)
        self.my_admins_list: List[Any] = []


TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("Токен бота не найден в переменных окружения")

bot = CustomBot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
