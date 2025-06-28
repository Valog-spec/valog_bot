from aiogram import Bot, types
from aiogram.filters import Filter

from logger.logger_helper import get_logger

logger = get_logger("logger.chat_types")


class ChatTypeFilter(Filter):
    """
    Фильтр для проверки типа чата.

    Позволяет ограничивать обработку сообщений определенными типами чатов
    (private, group, supergroup).

    Attributes:
        chat_types (list[str]): Список разрешенных типов чатов
    """

    def __init__(self, chat_types: list[str]) -> None:
        """
        Инициализирует фильтр с указанными типами чатов.

        Args:
            chat_types (list[str]): Список разрешенных типов чатов.
        """
        self.chat_types = chat_types
        logger.debug(f"Инициализирован ChatTypeFilter для типов: {chat_types}")

    async def __call__(self, message: types.Message) -> bool:
        """Проверяет, соответствует ли чат указанным типам"""
        logger.debug(f"Проверка типа чата: {message.chat.type}")
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    """
    Фильтр для проверки прав администратора.
    Проверяет, является ли отправитель сообщения администратором бота
    """

    def __init__(self) -> None:
        """Инициализирует фильтр для проверки администраторов"""
        logger.debug("Инициализирован IsAdmin фильтр")

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        """
        Проверяет, есть ли пользователь в списке администраторов.

        Args:
            message (types.Message): Входящее сообщение для проверки
            bot (Bot): Экземпляр бота для доступа к списку админов

        Returns:
            bool: True если пользователь администратор, иначе False
        """
        logger.debug(f"Проверка прав администратора")
        return message.from_user.id in bot.my_admins_list
