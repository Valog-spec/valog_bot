import asyncio

from aiogram import Dispatcher
from dotenv import find_dotenv, load_dotenv

from src.bot_instance import bot
from src.database.engine import create_db, session_maker
from src.handlers.admin.admin_private import admin_router
from src.handlers.group.user_group import user_group_router
from src.handlers.user.user_private import user_private_router
from src.logger.logger_helper import get_logger
from src.middlewares.db import DataBaseSession

load_dotenv(find_dotenv())

logger = get_logger("logger.app")

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup() -> None:
    """
    Функция инициализации при запуске бота
    """
    logger.info("Создание базы данных")
    await create_db()
    logger.info("База данных успешно создана")


async def main() -> None:
    logger.info("Настройка перед созданием")
    dp.startup.register(on_startup)

    logger.debug("Добавление Database middleware")
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Запуск бота в режиме polling")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
