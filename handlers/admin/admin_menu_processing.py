from typing import Any, Tuple, cast

from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner, Order
from database.orm_query import (
    delete_order,
    get_all_orders,
    get_order_by_order_id,
    orm_get_banner,
)
from kbds.inline.admin.inline_admin import (
    get_admin_keyboard,
    get_confirm_delete_keyboard,
    get_order_actions_keyboard,
    get_orders_keyboard,
    get_statuses_keyboard,
)
from logger.logger_helper import get_logger

logger = get_logger("loger.admin_menu_processing")


async def main(session: AsyncSession) -> Tuple[InputMediaPhoto | None, Any]:
    """
     Получает медиа-контент главного баннера и клавиатуру админа.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Tuple[InputMediaPhoto | None, Any]:
            - InputMediaPhoto: если баннер содержит изображение
            - None: если изображение отсутствует
            - Any: объект клавиатуры администратора
    """
    logger.debug("Запрос баннера 'main' из базы данных")
    banner = await orm_get_banner(session, "main")
    if not banner:
        error_msg = "Баннер не найден в базе данных"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug("Получение клавиатуры администратора")
    kbds = get_admin_keyboard()

    if banner.image:
        logger.debug("Создание InputMediaPhoto для баннера")
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
    else:
        image = None
        logger.info("Баннер не содержит изображение")
    logger.debug("Успешное завершение обработки главного баннера")
    return image, kbds


async def orders_list(session: AsyncSession) -> Tuple[InputMediaPhoto, Any]:
    """
    Формирует список заказов с баннером и  клавиатурой.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        tuple[InputMediaPhoto, Any]: Кортеж содержащий:
            - InputMediaPhoto: медиа-контент баннера заказов
            - Any:  клавиатуру для управления заказами
    """
    logger.debug("Запрос баннера 'orders' из БД")
    banner = cast(Banner, await orm_get_banner(session, "orders"))
    logger.debug("Создание InputMediaPhoto для баннера заказов")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    logger.debug("Запрос всех заказов из БД")
    orders = await get_all_orders(session)
    logger.debug("Получаем клавиатуру для заказов")
    kbds = get_orders_keyboard(orders)
    logger.info("Успешно сформирован список заказов")
    return image, kbds


async def view_order(
    order_id: int, session: AsyncSession
) -> Tuple[InputMediaPhoto, Any]:
    """
    Формирует представление конкретного заказа с баннером и клавиатурой

    Args:
        order_id (int): Идентификатор заказа для просмотра
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Tuple[InputMediaPhoto | None, Any]: Кортеж содержащий:
            - InputMediaPhoto: медиа-контент баннера заказов
            - Any: клавиатуру действий для заказа
    """
    logger.info("Формирование представления заказа ID: %d", order_id)

    logger.debug("Запрос баннера 'orders' из БД")

    banner = cast(Banner, await orm_get_banner(session, "orders"))

    logger.debug("Создание InputMediaPhoto для баннера заказов")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    logger.debug("Получение клавиатуры действий для заказа ID: %d", order_id)
    kbds = get_order_actions_keyboard(order_id)
    logger.info("Успешно сформировано представление для заказа ID: %d", order_id)
    return image, kbds


async def change_status(
    session: AsyncSession, order_id: int, status: str
) -> Tuple[InputMediaPhoto, Any]:
    """
    Изменяет статус заказа и возвращает обновленные данные для отображения

    Args:
    session (AsyncSession): Асинхронная сессия SQLAlchemy
    order_id (int): ID заказа для изменения
    status (str): Новый статус заказа (processing/shipped/delivered/cancelled)

    Returns:
        Tuple[InputMediaPhoto, Any]: Кортеж содержащий:
            - InputMediaPhoto: медиа-контент баннера заказов
            - Any: обновленную клавиатуру со списком заказов
    """

    logger.info("Изменение статуса заказа ID: %d на '%s'", order_id, status)

    logger.debug("Поиск заказа ID: %d", order_id)
    order = cast(Order, await get_order_by_order_id(order_id, session))
    kbds = get_statuses_keyboard(order_id)
    if status == "processing":
        order.status = "Обработка"
        await session.commit()
        orders = await get_all_orders(session)
        kbds = get_orders_keyboard(orders)
    elif status == "shipped":
        order.status = "Отправлен"
        await session.commit()
        orders = await get_all_orders(session)
        kbds = get_orders_keyboard(orders)

    elif status == "delivered":
        order.status = "Доставлен"
        await session.commit()
        orders = await get_all_orders(session)
        kbds = get_orders_keyboard(orders)

    elif status == "cancelled":
        await delete_order(session, order_id)
        orders = await get_all_orders(session)
        kbds = get_orders_keyboard(orders)

    logger.info("Статус изменен")

    logger.debug("Получение баннера 'orders'")
    banner = cast(Banner, await orm_get_banner(session, "orders"))

    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    logger.info("Успешно изменен статус заказа ID: %d", order_id)
    return image, kbds


async def order_delete(
    session: AsyncSession, order_id: int
) -> Tuple[InputMediaPhoto | None, Any]:
    kbds = get_confirm_delete_keyboard(order_id)

    banner = cast(Banner, await orm_get_banner(session, "orders"))

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


async def confirm_delete(
    session: AsyncSession, order_id: int
) -> Tuple[InputMediaPhoto, Any]:
    """
    Подготавливает данные для подтверждения удаления заказа

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        order_id (int): ID заказа для удаления

     Returns:
        Tuple[InputMediaPhoto | None, Any]: Кортеж содержащий:
            - InputMediaPhoto: медиа-контент баннера заказов
            - Any: клавиатуру подтверждения удаления
    """
    logger.debug("Запрос баннера 'orders' из БД")
    banner = cast(Banner, await orm_get_banner(session, "orders"))

    logger.debug("Создание InputMediaPhoto для баннера заказов")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    logger.info("Успешно подготовлено подтверждение удаления заказа ID: %d", order_id)
    await delete_order(session, order_id)
    orders = await get_all_orders(session)
    kbds = get_orders_keyboard(orders)

    return image, kbds


async def get_admin_menu_content(
    session: AsyncSession,
    action: str | None = None,
    order_id: int | None = None,
    status: str | None = None,
) -> tuple[InputMediaPhoto | None, Any] | None:
    """
    Роутер для получения контента

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        action (str | None): Тип запрашиваемого действия
        order_id (int | None): ID заказа
        status (str | None): Новый статус заказа

    Returns:
        Tuple[InputMediaPhoto, Any] | None: Кортеж (медиа, клавиатура) или None
            - InputMediaPhoto: медиа-контент баннера
            - Any: соответствующая клавиатура
    """
    logger.info(
        "Запрос контента админ-меню. Действие: %s OrderID: %d, Статус: %s",
        action,
        order_id,
        status,
    )
    if action == "main":
        return cast(Tuple[InputMediaPhoto, Any], await main(session))
    elif action == "list_orders":
        return cast(Tuple[InputMediaPhoto, Any], await orders_list(session))
    elif action == "view":
        return cast(Tuple[InputMediaPhoto, Any], await view_order(order_id, session))  # type: ignore[arg-type]
    elif action == "edit_status":
        return cast(Tuple[InputMediaPhoto, Any], await change_status(session, order_id, status))  # type: ignore[arg-type]
    elif action == "delete":
        return cast(Tuple[InputMediaPhoto, Any], await order_delete(session, order_id))  # type: ignore[arg-type]
    elif action == "confirm_delete":
        return cast(Tuple[InputMediaPhoto, Any], await confirm_delete(session, order_id))  # type: ignore[arg-type]
    else:
        return None
