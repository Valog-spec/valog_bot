import os
from typing import cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common import categories, description_for_info_pages
from database.models import Base
from database.orm_query import orm_add_banner_description, orm_create_categories
from logger.logger_helper import get_logger

logger = get_logger("logger.engine")

db_url = os.getenv("DB_SQL")
if not db_url:
    logger.error("Не задана переменная окружения DB_SQL")
    raise ValueError("Не задана переменная окружения DB_SQL")

engine: AsyncEngine = cast(AsyncEngine, create_async_engine(db_url, echo=False))

session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def create_db() -> None:
    """
    Инициализирует базу данных и заполняет начальными данными
    """
    logger.info("Начало инициализации базы данных")
    try:
        logger.debug("Создание таблиц в базе данных")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы успешно созданы")

        logger.debug("Заполнение базы начальными данными")
        async with session_maker() as session:
            logger.debug("Добавление категорий")
            await orm_create_categories(session, categories)
            logger.debug("Добавление описаний баннеров")
            await orm_add_banner_description(session, description_for_info_pages)
    except SQLAlchemyError as exc:
        logger.error("Ошибка SQLAlchemy при работе с базой данных: %s", exc)
    except Exception as exc:
        logger.exception("Ошибка при инициализации базы данных", exc_info=exc)
        raise


async def drop_db() -> None:
    """
    Удаление базы данных
    """
    logger.warning("Начало удаления таблиц из базы данных")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("Все таблицы успешно удалены")
    except SQLAlchemyError as exc:
        logger.error("Ошибка при удалении таблиц базы данных %s", exc)
    except Exception as exc:
        logger.critical("Неожиданная ошибка при удалении таблиц", exc_info=exc)
        raise
