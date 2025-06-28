
from aiogram import Bot, Router, types
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter
from logger.logger_helper import get_logger

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))
user_group_router.edited_message.filter(ChatTypeFilter(["group", "supergroup"]))


logger = get_logger("logger.user_group")


@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot) -> None:
    """
    Обработчик команды /admin для получения списка администраторов чата.

    Args:
       message (types.Message): Входящее сообщение с командой
       bot (Bot): Экземпляр бота
    """
    logger.info(
        "Запуск команды /admin в чате %d (тип: %s)", message.chat.id, message.chat.id
    )
    chat_id = message.chat.id
    logger.debug("Получение администраторов для чата ID: %d", chat_id)
    admins_list = await bot.get_chat_administrators(chat_id)
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list  # type: ignore[attr-defined]
    logger.debug("Список админов сохранен: %s", admins_list)
    if message.from_user.id in admins_list:  # type: ignore[operator]
        logger.info("Сообщение от админа %d будет удалено", message.from_user.id)
        await message.delete()
        logger.debug("Сообщение успешно удалено")
