import asyncio

from aiogram import Bot, Dispatcher
from dotenv import find_dotenv, load_dotenv

from bot_instance import bot

load_dotenv(find_dotenv())

from database.engine import create_db, session_maker
from handlers.admin.admin_private import admin_router
from handlers.group.user_group import user_group_router
from handlers.user.user_private import user_private_router
from logger.logger_helper import get_logger
from middlewares.db import DataBaseSession

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
