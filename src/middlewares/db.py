from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    """
    Middleware для предоставления сессии базы данных

    Attributes:
        session_pool (async_sessionmaker): Фабрика для создания асинхронных сессий БД
    """

    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обрабатывает событие, предоставляя сессию БД в контексте обработки.

        Args:
            handler: Следующий обработчик в цепочке middleware
            event: Объект Telegram-события
            data: Словарь с данными для обработчиков
        """
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
