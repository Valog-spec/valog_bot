from typing import Any, Tuple

from aiogram.types import InputMediaPhoto, LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    delete_order,
    orm_add_to_cart,
    orm_create_order,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_categories,
    orm_get_orders,
    orm_get_product,
    orm_get_products,
    orm_get_user_carts,
    orm_reduce_product_in_cart,
)
from kbds.inline.user.inline import (
    get_products_btns,
    get_user_cart,
    get_user_catalog_btns,
    get_user_main_btns,
    get_user_orders,
)
from logger.logger_helper import get_logger
from payments.ukassa import create_payment
from utils.paginator import Paginator

logger = get_logger("logger.user_menu_processing")


async def main_menu(
    session: AsyncSession, level: int, menu_name: str
) -> Tuple[InputMediaPhoto, Any]:
    """
     Генерирует главное меню с баннером

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        level (int): Уровень меню
        menu_name (str): Название меню для загрузки баннера

    Returns:
        Tuple[InputMediaPhoto, Any]: Медиа-объект с баннером и клавиатура
    """
    banner = await orm_get_banner(session, menu_name)
    logger.info(f"Баннер '{menu_name}' успешно загружен")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)
    logger.debug("Получено главное меню")

    return image, kbds


async def catalog(
    session: AsyncSession, level: int, menu_name: str
) -> Tuple[InputMediaPhoto, Any]:
    """
    Генерирует меню каталога с категориями товаров

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        level (int): Уровень меню
        menu_name (str): Название меню для загрузки баннера

    Returns:
        Tuple[InputMediaPhoto, Any]: Медиа-объект с баннером и клавиатура с категориями
    """
    logger.debug(f"Получение каталога. Уровень: {level}, Меню: '{menu_name}'")
    banner = await orm_get_banner(session, menu_name)
    logger.info(f"Баннер каталога '{menu_name}' успешно загружен")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(level=level, categories=categories)
    logger.debug(f"Получен каталог с категориями")

    return image, kbds


def pages(paginator: Paginator) -> Any:
    """
    Генерирует кнопки пагинации (предыдущая/следующая страницы)

    Args:
       paginator (Paginator): Объект пагинатора с информацией о текущей странице

    Returns:
       Any: Словарь с кнопками навигации
    """
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def products(
    session: AsyncSession, level: int, category: int, page: int
) -> Tuple[InputMediaPhoto, Any]:
    """
    Генерирует страницу с товаром для каталога

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        level (int): Уровень меню (для формирования кнопок)
        category (int): ID категории товаров
        page (int): Номер текущей страницы

    Returns:
        Tuple[InputMediaPhoto, Any]: Медиа-объект с фото товара и клавиатура
    """
    logger.info(f"Формирование страницы товара, Страница: {page}, Уровень: {level}")

    logger.debug(f"Запрос товаров категории {category}")
    products = await orm_get_products(session, category_id=category)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]
    logger.debug(f"Пагинация: страница {paginator.page} из {paginator.len}")

    image = InputMediaPhoto(
        media=product.image,
        caption=f"<strong>{product.name}\
                </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}\n\
                <strong>Товар {paginator.page} из {paginator.len}</strong>",
    )
    logger.debug(f"Карточка товара ID: {product.id}")
    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )
    logger.info("Кнопки навигации успешно получены")

    return image, kbds


async def carts(
    session: AsyncSession,
    level: int,
    menu_name: str,
    page: int,
    user_id: int,
    product_id: int,
) -> Tuple[InputMediaPhoto, Any]:
    """
    Обрабатывает корзину пользователя: отображение, добавление/удаление товаров

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        level (int): Уровень меню
        menu_name (str): Тип операции ("delete", "decrement", "increment")
        page (int): Номер текущей страницы
        user_id (int): ID пользователя Telegram
        product_id (int): ID товара для операций

    Returns:
        Tuple[InputMediaPhoto, Any]: Медиа-объект с фото товара и клавиатура
    """
    logger.info(
        f"Обработка корзины. User: {user_id},"
        f"Операция: {menu_name}, Товар: {product_id}, Страница: {page}"
    )
    if menu_name == "delete":
        logger.debug(f"Удаление товара {product_id} из корзины пользователя {user_id}")
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1
            logger.debug(f"Уменьшение номера страницы до {page} после удаления")
    elif menu_name == "decrement":
        logger.debug(
            f"Уменьшение количества товара {product_id} в корзине пользователя {user_id}"
        )
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart:
            page -= 1
            logger.debug(
                f"Уменьшение номера страницы до {page} после уменьшения количества"
            )
    elif menu_name == "increment":
        logger.debug(
            f"Увеличение количества товара {product_id} в корзине пользователя {user_id}"
        )
        await orm_add_to_cart(session, user_id, product_id)

    carts = await orm_get_user_carts(session, user_id)

    if not carts:
        logger.debug("Корзина пуста - отображение пустой корзины")
        banner = await orm_get_banner(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        kbds = get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
            product_id=None,
        )

    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(
            sum(cart.quantity * cart.product.price for cart in carts), 2
        )

        logger.debug(
            f"Формирование страницы корзины. Товар: {cart.product.name},"
            f"Количество: {cart.quantity}, Цена: {cart_price},"
            f"Общая стоимость: {total_price}"
        )
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n{cart.product.price}$ x {cart.quantity} = {cart_price}$\
                    \nТовар {paginator.page} из {paginator.len} в корзине.\nОбщая стоимость товаров в корзине {total_price}",
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds


async def order(
    session: AsyncSession, user_id: int, data: dict
) -> Tuple[InputMediaPhoto, Any]:
    """
    Обрабатывает создание нового заказа и возвращает в главное меню

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        user_id (int): ID пользователя в Telegram(е)
        data (dict): Данные заказа

    Returns:
        Tuple[InputMediaPhoto, Any]: Медиа-объект с баннером главного меню и клавиатура
    """
    logger.info(f"Начало cозданя заказа для пользователя {user_id}")
    await orm_create_order(user_id, data, session)
    logger.info(f"Заказ для пользователя {user_id} создан")

    banner = await orm_get_banner(session, "main")
    logger.debug("Баннер главного меню загружен")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=0)
    logger.info(
        f"Пользователь {user_id} возвращен в главное меню после создания заказа"
    )

    return image, kbds


async def my_orders(
    session: AsyncSession, level: int, page: int, user_id: int
) -> Tuple[InputMediaPhoto, Any]:
    """
    Обрабатывает отображение заказов пользователя

    Args:
       session (AsyncSession): Асинхронная сессия для работы с БД
       level (int): Уровень меню
       page (int): Номер текущей страницы пагинации
       user_id (int): ID пользователя в Telegram(е)

    Returns:
       Tuple[InputMediaPhoto, Any]: Медиа-объект с информацией о заказе и клавиатура

    """

    logger.info(f"Запрос заказов пользователя {user_id}. Страница {page}")

    logger.debug(f"Получение заказов для пользователя {user_id}")
    my_orders = await orm_get_orders(session, user_id)

    if not my_orders:

        logger.debug("У пользователя нет заказов - отображение пустой истории")
        banner = await orm_get_banner(session, "orders")

        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}:\nпусто</strong>"
        )
        kbds = get_user_orders(
            level=level, page=None, pagination_btns=None, product_id=None, order_id=None
        )
    else:
        paginator = Paginator(my_orders, page=page)
        order = paginator.get_page()[0]
        product = await orm_get_product(session, order.product_id)

        logger.debug(f"Отображение заказа ID: {order.id}.Товар: {product.name}")
        image = InputMediaPhoto(
            media=product.image,
            caption=f"<strong>{product.name}</strong>\n{product.description}"
            f"\n{order.status}\nОплачен:{order.paid}\nК оплате{order.total_price}",
        )
        pagination_btns = pages(paginator)

        kbds = get_user_orders(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=product.id,
            order_id=order.id,
        )

    return image, kbds


async def delete_order_user(
    session: AsyncSession, order_id: int, level: int, page: int, user_id: int
) -> Tuple[InputMediaPhoto, Any]:
    """
    Удаляет заказ пользователя и возвращает обновленный список заказов

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        order_id (int): ID удаляемого заказа
        level (int): Уровень меню
        page (int): Номер текущей страницы пагинации
        user_id (int): ID пользователя, чей заказ удаляется
    """
    await delete_order(session, order_id)
    logger.info(f"Заказ {order_id} успешно удален")

    image, kbds = await my_orders(session, level, page, user_id)
    logger.info("Успешно возвращен обновленный список заказов")

    return image, kbds


async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
    product_id: int | None = None,
    order_id: int | None = None,
    user_id: int | None = None,
    data: dict | None = None,
) -> Tuple[InputMediaPhoto, Any] | None:
    """
     Центральный роутер для получения контента меню разных уровней.

    Args:
        session (AsyncSession): Асинхронная сессия для работы с БД
        level (int): Уровень меню
        menu_name (str): Название меню/баннера
        category (int | None): ID категории
        page (int | None): Номер страницы пагинации
        product_id (int | None): ID товара
        order_id (int | None): ID заказа
        user_id (int | None): ID пользователя
        data (dict | None): Дополнительные данные

    Returns:
        Tuple[InputMediaPhoto, Any] | None: Контент меню или None если уровень неизвестен
    """
    logger.info(
        f"Запрос контента меню пользователя. Уровень: {level} OrderID: {order_id}"
    )
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await products(session, level, category, page)
    elif level == 3:
        return await carts(session, level, menu_name, page, user_id, product_id)
    elif level == 4:
        return await order(session, user_id, data)
    elif level == 5:
        return await my_orders(session, level, page, user_id)
    elif level == 7:
        return await delete_order_user(session, order_id, level, page, user_id)
    else:
        return None
