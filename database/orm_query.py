from typing import Any, Coroutine, List, Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot_instance import bot
from database.models import Banner, Cart, Category, Order, Product, User
from logger.logger_helper import get_logger

logger = get_logger("logger.orm_query")


async def orm_add_banner_description(session: AsyncSession, data: dict) -> None:
    """
    Добавляет описания баннеров в базу данных, если они отсутствуют.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        data (dict): Словарь с данными баннеров
    """
    logger.debug(f"Попытка добавить описания баннеров: {list(data.keys())}")
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        logger.info("Описания баннеров уже существуют, пропускаем добавление")
        return
    session.add_all(
        [
            Banner(name=name, description=description)
            for name, description in data.items()
        ]
    )
    await session.commit()
    logger.info("Баннеры успешно добавлены")


async def orm_change_banner_image(session: AsyncSession, name: str, image: str) -> None:
    """
    Обновляет изображение для указанного баннера.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        name (str): Название баннера для обновления
        image (str): Новое изображение

    Raises:
        ValueError: Если баннер с указанным именем не найден
    """
    logger.debug(f"Запрос на обновление изображения баннера '{name}'")
    query = update(Banner).where(Banner.name == name).values(image=image)
    result = await session.execute(query)
    if result.rowcount == 0:
        error_msg = f"Баннер с именем '{name}' не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    await session.commit()
    logger.info(f"Изображение баннера '{name}' успешно обновлено")


async def orm_get_banner(session: AsyncSession, page: str) -> Banner:
    """
    Получает баннер по названию страницы.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       page (str): Название страницы (баннера)

    Returns:
       Banner: Объект баннера
    """
    logger.debug(f"Запрос баннера для страницы '{page}'")
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    banner = result.scalar()

    if banner:
        logger.debug(f"Баннер '{page}' найден")
    else:
        logger.debug(f"Баннер '{page}' не найден")

    return banner


async def orm_get_info_pages(session: AsyncSession) -> Sequence[Banner]:
    """
    Получает список всех баннеров.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Sequence[Banner]: Последовательность объектов баннеров
    """
    logger.debug("Запрос всех баннеров")
    query = select(Banner)
    result = await session.execute(query)
    logger.info("Все баннеры получены")
    return result.scalars().all()


async def orm_get_categories(session: AsyncSession) -> Sequence[Category]:
    """
    Получает список всех категорий товаров.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Sequence[Category]: Последовательность объектов категорий
    """
    logger.debug("Запрос всех категорий товаров")
    query = select(Category)
    result = await session.execute(query)
    logger.info("Все категории товаров получены")
    return result.scalars().all()


async def orm_create_categories(session: AsyncSession, categories: list) -> None:
    """
    Создает категории товаров в базе данных, если они отсутствуюn

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        categories (list[str]): Список названий категорий для создания
    """
    logger.debug(f"Попытка создать категории: {categories}")
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        logger.info("Категории уже существуют, пропускаем создание")
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()
    logger.info("Все категории успешно созданы")


async def orm_add_product(session: AsyncSession, data: dict) -> None:
    """
     Добавляет новый товар в базу данных.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        data (dict): Данные товара

    """
    try:
        obj = Product(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"]),
        )
        session.add(obj)
        await session.commit()
        logger.info(f"Товар '{data['name']}' успешно добавлен (ID: {obj.id})")
    except (KeyError, ValueError) as exc:
        logger.exception("Ошибка добавления товара", exc_info=exc)


async def orm_get_products(
    session: AsyncSession, category_id: int
) -> Sequence[Product]:
    """
    Получает список товаров по ID категории.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       category_id (int): ID категории для фильтрации

    Returns:
       list[Product]: Список объектов товаров или пустой список, если не найдено
    """
    logger.debug(f"Запрос товаров категории ID: {category_id}")
    query = select(Product).where(Product.category_id == category_id)
    result = await session.execute(query)
    logger.info("Товары найдены")
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int) -> Product | None:
    """
    Получает товар по его идентификатору.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       product_id (int): ID товара для поиска

    Returns:
       Product | None: Объект товара либо None, если товар не найден
    """
    logger.debug(f"Запрос товара с ID: {product_id}")
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar()
    if product:
        logger.info(f"Товар найден - ID: {product_id}, Название: {product.name}")
    else:
        logger.warning(f"Товар с ID {product_id} не найден")
    return product


async def orm_update_product(
    session: AsyncSession, product_id: int, data: dict
) -> None:
    """
    Обновляет данные товара

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       product_id (int): ID товара для обновления
       data (dict): Словарь с новыми данными товара

    Raises:
       ValueError: Если товар не найден или неверные данные
       KeyError: Если отсутствуют обязательные поля
    """
    logger.info(f"Обновление товара ID: {product_id}, данные: {data}")
    try:
        product = await orm_get_product(session, product_id)
        if not product:
            raise ValueError(f"Товар с ID {product_id} не найден")
        query = (
            update(Product)
            .where(Product.id == product_id)
            .values(
                name=data["name"],
                description=data["description"],
                price=float(data["price"]),
                image=data["image"],
                category_id=int(data["category"]),
            )
        )
        await session.execute(query)
        await session.commit()
        logger.info(f"Товар ID: {product_id} успешно обновлен")
    except (KeyError, ValueError) as exc:
        error_msg = f"Ошибка обновления товара ID {product_id}: {str(exc)}"
        logger.exception(error_msg, exc_info=exc)


async def orm_delete_product(session: AsyncSession, product_id: int) -> None:
    """
    Удаляет товар из базы данных.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       product_id (int): ID товара для удаления

    Raises:
       ValueError: Если товар не найден
    """
    logger.warning(f"Запрос на удаление товара ID: {product_id}")
    product = await orm_get_product(session, product_id)
    if not product:
        error_msg = f"Товар с ID {product_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()
    logger.warning(f"Товар ID: {product_id} успешно удален")


async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    """
    Добавляет нового пользователя в базу данных, если он не существует.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        user_id (int): Уникальный идентификатор пользователя в Telegram(е)
        first_name (str | None): Имя пользователя
        last_name (str | None): Фамилия пользователя
    """
    logger.debug(f"Попытка добавить пользователя: user_id={user_id}")
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(User(user_id=user_id, first_name=first_name, last_name=last_name))
        await session.commit()
        logger.info(
            f"Добавлен новый пользователь: user_id={user_id}, имя={first_name} {last_name}"
        )
    else:
        logger.debug(
            f"Пользователь user_id={user_id} уже существует, пропускаем добавление"
        )


async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int) -> None:
    """
    Добавляет товар в корзину пользователя или увеличивает количество, если уже есть.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        user_id (int): ID пользователя
        product_id (int): ID товара

    Raises:
        ValueError: Если пользователь или товар не существуют
    """
    logger.debug(
        f"Добавление товара product_id={product_id} в корзину user_id={user_id}"
    )
    user = await session.get(User, user_id)
    product = await session.get(Product, product_id)

    if not user:
        error_msg = f"Пользователь user_id={user_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not product:
        error_msg = f"Товар product_id={product_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        logger.info(
            f"Увеличено количество товара product_id={product_id} в корзине user_id={user_id}"
        )
        cart.quantity += 1
        await session.commit()
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()
        logger.info(
            f"Добавлен новый товар product_id={product_id} в корзину user_id={user_id}"
        )


async def orm_get_user_carts(session: AsyncSession, user_id: int) -> Sequence[Cart]:
    """
    Получает все товары в корзине пользователя с полной информацией о продуктах.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД
       user_id (int): Идентификатор пользователя, чью корзину запрашиваем

    Returns:
       Sequence[Cart]: Список объектов корзины о товарах или пустой список, если корзина пуста

    Raises:
       ValueError: Если пользователь с указанным ID не существует
    """
    logger.debug(f"Запрос содержимого корзины для пользователя user_id={user_id}")
    user_exists = await session.get(User, user_id)

    if not user_exists:
        error_msg = f"Пользователь с user_id={user_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)
    try:
        query = (
            select(Cart)
            .filter(Cart.user_id == user_id)
            .options(joinedload(Cart.product))
        )
        result = await session.execute(query)
        logger.info(f"Найдены товары в корзине пользователя user_id={user_id}")
        return result.scalars().all()
    except Exception as exc:
        error_msg = (
            f"Ошибка при получении корзины пользователя user_id={user_id}: {str(exc)}"
        )
        logger.exception(error_msg, exc_info=exc)
        raise


async def orm_delete_from_cart(
    session: AsyncSession, user_id: int, product_id: int
) -> None:
    """
    Удаляет товар из корзины пользователя

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       user_id (int): ID пользователя из чьей корзины нужно удалить
       product_id (int): ID товара для удаления из корзины


    Raises:
       ValueError: Если пользователь не существует
    """
    if not await session.get(User, user_id):
        error_msg = f"Пользователь user_id={user_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()
    logger.info(
        f"Товар product_id={product_id} успешно удален из корзины user_id={user_id}"
    )


async def orm_reduce_product_in_cart(
    session: AsyncSession, user_id: int, product_id: int
) -> bool | None:
    """
    Уменьшает количество товара в корзине или удаляет его, если количество = 1.

    Args:
      session (AsyncSession): Асинхронная сессия SQLAlchemy
      user_id (int): ID пользователя
      product_id (int): ID товара

    Returns:
      bool:
          - True: если количество уменьшено
          - False: если товар удален из корзины
    """
    logger.info(
        f"Уменьшение количества товара product_id={product_id} в корзине user_id={user_id}"
    )
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        logger.debug(
            f"Товар product_id={product_id} не найден в корзине user_id={user_id}"
        )
        return None
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        logger.info(
            f"Уменьшено количество товара product_id={product_id} в корзине user_id={user_id}."
            f"Новое количество: {cart.quantity}"
        )
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        logger.info(
            f"Удаление товара product_id={product_id}из корзины user_id={user_id}"
        )
        return False


async def orm_get_cart(session: AsyncSession, user_id: int, product_id: int) -> Cart:
    """
    Получает запись о товаре в корзине пользователя.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД
        user_id (int): Идентификатор пользователя
        product_id (int): Идентификатор товара

    Returns:
        Cart: Объект Cart
    """
    logger.debug(
        f"Запрос товара product_id={product_id} в корзине пользователя user_id={user_id}"
    )
    query = select(Cart).filter(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    logger.debug(f"Найден товар product_id={product_id} в корзине user_id={user_id}")
    return cart.scalar()


async def orm_create_order(user_id: int, data: dict, session: AsyncSession) -> None:
    """
    Создает новый заказ на основе данных корзины и информации о клиенте и отправляет уведомление об этом админам

    Args:
        user_id (int): Telegram ID пользователя
        data (dict): Уникальный идентификатор пользователя Telegram
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Raises:
        ValueError: Если товар или корзина не найдены
    """
    logger.info(f"Создание заказа для user_id={user_id}")
    logger.debug(f"Поиск товара product_id={data['product_id']} в корзине")
    cart = await orm_get_cart(session, user_id, data["product_id"])
    if not cart:
        error_msg = f"Товар product_id={data['product_id']} не найден в корзине"
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.debug(f"Получение информации о товаре product_id={data['product_id']}")

    product = await orm_get_product(session, data["product_id"])
    if not product:
        error_msg = f"Товар product_id={data['product_id']} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    order = Order(
        user_id=user_id,
        full_name=data["full_name"],
        status="В обработке",
        address=data["address"],
        phone=data["phone"],
        product_id=data["product_id"],
        total_price=cart.quantity * product.price,
    )
    session.add(order)

    await session.commit()
    logger.info(f"Заказ #{order.id} успешно создан")

    try:
        await bot.send_message(
            chat_id=1677148093,
            text=f"""🛒<b>Новый заказ #{order.id}</b>
                    👤 Клиент: {order.full_name}
                    📞 Телефон: {order.phone}
                    📍 Адрес: {order.address}
                    💰 Сумма: {order.total_price} руб.
                    🕒 Время: {order.created}""",
            parse_mode="HTML",
        )
        logger.info(f"Уведомление о заказе #{order.id} отправлено админу {1677148093}")
    except Exception as exc:
        logger.exception(
            f"Ошибка отправки уведомления админу {1677148093}", exc_info=exc
        )


async def orm_get_orders(session: AsyncSession, user_id: int) -> Sequence[Order]:
    """
    Получает список всех заказов пользователя.

    Args:
       session (AsyncSession): Асинхронная сессия SQLAlchemy
       user_id (int): ID пользователя для фильтрации заказов

    Returns:
       Sequence[Order]: Список заказов пользователя или пустой список
    """
    logger.info(f"Запрос заказов для пользователя user_id={user_id}")
    try:
        query = select(Order).where(Order.user_id == user_id)
        result = await session.execute(query)
        logger.debug(f"Заказы для user_id={user_id} найдены")
        return result.scalars().all()
    except Exception as exc:
        logger.exception(
            f"Ошибка получения заказов для user_id={user_id}", exc_info=exc
        )
        raise


async def get_order_by_order_id(order_id: int, session: AsyncSession) -> Order | None:
    """
    Получает заказ по его ID.

    Args:
        order_id (int): ID заказа
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Order | None: Объект заказа или None если не найден
    """
    order = await session.get(Order, order_id)
    try:
        if not order:
            logger.warning(f"Заказ order_id={order_id} не найден")
        return order
    except Exception as exc:
        logger.exception(f"Ошибка получения заказа order_id={order_id}", exc_info=exc)
        raise


async def get_all_orders(session: AsyncSession) -> Sequence[Order]:
    """
    Получает список всех заказов в системе.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    Returns:
        Sequence[Order]: Последовательность всех заказов или пустой список
    """
    logger.info("Запрос всех заказов в системе")
    try:
        query = select(Order)
        result = await session.execute(query)
        logger.debug(f"Все заказы найдены")
        return result.scalars().all()
    except Exception as exc:
        logger.exception(f"Ошибка получения всех заказов", exc_info=exc)
        raise


async def delete_order(session: AsyncSession, order_id: int) -> None:
    """
    Удаляет заказ по его ID

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        order_id (int): ID заказа для удаления
    """
    logger.warning(f"Запрос на удаление заказа order_id={order_id}")
    order = await get_order_by_order_id(order_id, session)
    if not order:
        logger.warning(f"Заказ order_id={order_id} не найден, удаление невозможно")
        return
    await session.delete(order)
    await session.commit()
    logger.info(f"Заказ order_id={order_id} успешно удален")


async def change_order(session: AsyncSession, order_id: int) -> None:
    """
    Изменяет статус заказа на 'Оплачен'.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        order_id (int): ID заказа для изменения

    Raises:
        ValueError: Если заказ не найден
    """
    logger.info(f"Изменение статуса заказа order_id={order_id} на 'Оплачен'")
    order = await get_order_by_order_id(order_id, session)
    if not order:
        error_msg = f"Заказ order_id={order_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)
    order.paid = True
    await session.commit()
    logger.info(f"Статус заказа order_id={order_id} успешно изменен на 'Оплачен'")


async def orm_get_total_price(session: AsyncSession, order_id: int) -> float:
    """
    Получает общую сумму заказа.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        order_id (int): ID заказа

    Returns:
        float: Сумма заказа

    Raises:
        ValueError: Если заказ не найден
    """
    logger.debug(f"Запрос суммы заказа order_id={order_id}")
    order = await get_order_by_order_id(order_id, session)
    if not order:
        error_msg = f"Заказ order_id={order_id} не найден"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return order.total_price
