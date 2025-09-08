from typing import Any, Dict, Sequence, cast

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallBack(CallbackData, prefix="menu"):
    """
    Класс для обработки callback-данных меню и навигации.

    Attributes:
        level (int): Текущий уровень вложенности меню
        menu_name (str): Название/идентификатор текущего меню
        category (int | None): ID категории
        page (int): Номер страницы для пагинации
        product_id (int | None): ID товара
        order_id (int | None): ID заказа
    """

    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    product_id: int | None = None
    order_id: int | None = None


def get_user_main_btns(
    *, level: int, sizes: tuple[int] = (2,)
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает главное меню пользователя с основными разделами

    Args:
        level (int): Текущий уровень вложенности меню
        sizes (tuple[int], optional): Распределение кнопок по рядам

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Товары 🍔": "catalog",
        "Корзина 🛒": "cart",
        "О нас ℹ️": "about",
        # "Оплата 💰": "payment",
        "Доставка ⛵": "shipping",
        "Мои заказы": "orders",
        "Написать в поддержку": "support",
    }
    for text, menu_name in btns.items():
        if menu_name == "catalog":
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level + 1, menu_name=menu_name
                    ).pack(),
                )
            )
        elif menu_name == "cart":
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=3, menu_name=menu_name).pack(),
                )
            )
        elif menu_name == "orders":
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=5, menu_name=menu_name).pack(),
                )
            )
        else:
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=level, menu_name=menu_name).pack(),
                )
            )

    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_btns(
    *, level: int, categories: Sequence, sizes: tuple[int] = (2,)
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает меню каталога с категориями товаров

    Args:
        level (int): Текущий уровень вложенности меню
        categories (Sequence): Список категорий для отображения
        sizes (tuple[int], optional): Распределение кнопок по рядам
    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MenuCallBack(level=level - 1, menu_name="main").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="cart").pack(),
        )
    )

    for c in categories:
        keyboard.add(
            InlineKeyboardButton(
                text=c.name,
                callback_data=MenuCallBack(
                    level=level + 1, menu_name=c.name, category=c.id
                ).pack(),
            )
        )

    return keyboard.adjust(*sizes).as_markup()


def get_products_btns(
    *,
    level: int,
    category: int,
    page: int,
    pagination_btns: dict,
    product_id: int,
    sizes: tuple[int, int] = (2, 1),
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру для работы с конкретным товаром

    Args:
        level (int): Текущий уровень вложенности
        category (int): ID текущей категории
        page (int): Номер текущей страницы
        pagination_btns (dict): Кнопки пагинации
        product_id (int): ID текущего товара
        sizes (tuple[int]): Распределение кнопок

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MenuCallBack(level=level - 1, menu_name="catalog").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="cart").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="В коризину 💵",
            callback_data=MenuCallBack(
                level=level, menu_name="add_to_cart", product_id=product_id
            ).pack(),
        )
    )

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        category=category,
                        page=page + 1,
                    ).pack(),
                )
            )

        elif menu_name == "previous":
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        category=category,
                        page=page - 1,
                    ).pack(),
                )
            )

    return keyboard.row(*row).as_markup()


def get_user_cart(
    *,
    level: int,
    page: int | None,
    pagination_btns: dict | None,
    product_id: int | None,
    sizes: tuple[int] = (3,),
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру для работы с корзиной

    Args:
       level (int): Текущий уровень вложенности
       page (int | None): Номер страницы или None если корзина пуста
       pagination_btns (dict | None): Кнопки пагинации или None
       product_id (int | None): ID товара или None
       sizes (tuple[int], optional): Распределение кнопок

    Returns:
       InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(
            InlineKeyboardButton(
                text="Удалить",
                callback_data=MenuCallBack(
                    level=level, menu_name="delete", product_id=product_id, page=page
                ).pack(),
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                text="-1",
                callback_data=MenuCallBack(
                    level=level, menu_name="decrement", product_id=product_id, page=page
                ).pack(),
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                text="+1",
                callback_data=MenuCallBack(
                    level=level, menu_name="increment", product_id=product_id, page=page
                ).pack(),
            )
        )

        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in cast(Dict[Any, Any], pagination_btns).items():
            if menu_name == "next":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page + 1
                        ).pack(),
                    )
                )
            elif menu_name == "previous":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page - 1
                        ).pack(),
                    )
                )

        keyboard.row(*row)

        # add_carts = InlineKeyboardButton(
        #     text="Добавить в заказ",
        #     callback_data=MenuCallBack(level=level, menu_name="cart").pack()
        # )
        # keyboard.row(add_carts)

        row2 = [
            InlineKeyboardButton(
                text="На главную 🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            ),
            InlineKeyboardButton(
                text="Заказать",
                callback_data=MenuCallBack(
                    level=4, product_id=product_id, menu_name="order"
                ).pack(),
            ),
        ]
        return keyboard.row(*row2).as_markup()
    else:
        keyboard.add(
            InlineKeyboardButton(
                text="На главную 🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            )
        )

        return keyboard.adjust(*sizes).as_markup()


# def get_user_order(
#         *,
#         level: int,
#         page: int | None,
#         pagination_btns: dict | None,
#         product_id: int | None,
#         sizes: tuple[int] = (3,)
# ) -> InlineKeyboardMarkup:
#
#     keyboard = InlineKeyboardBuilder()
#     keyboard.add(InlineKeyboardButton(text='назад',
#                                       callback_data=MenuCallBack(level=level, menu_name='delete',
#                                                                  product_id=product_id, page=page).pack()))
#     keyboard.add(InlineKeyboardButton(text='-1',
#                                       callback_data=MenuCallBack(level=level, menu_name='decrement',
#                                                                  product_id=product_id, page=page).pack()))
#     keyboard.add(InlineKeyboardButton(text='+1',
#                                       callback_data=MenuCallBack(level=level, menu_name='increment',
#                                                                  product_id=product_id, page=page).pack()))
#
#     keyboard.adjust(*sizes)
#
#     return keyboard.adjust(*sizes).as_markup()

#
# def get_user_orders_btns(*, sizes: tuple[int] = (2,)) -> InlineKeyboardMarkup:
#     keyboard = InlineKeyboardBuilder()
#     keyboard.add(InlineKeyboardButton(text='назад',
#                                       callback_data=MenuCallBack(level=0, menu_name='main').pack()))
#
#     keyboard.adjust(*sizes)
#
#     return keyboard.adjust(*sizes).as_markup()


def get_user_orders(
    *,
    level: int,
    page: int | None,
    pagination_btns: dict | None,
    product_id: int | None,
    order_id: int | None,
    sizes: tuple[int] = (3,),
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру для работы с заказами пользователя

    Args:
        level (int): Текущий уровень вложенности
        page (int | None): Номер страницы или None
        pagination_btns (dict | None): Кнопки пагинации или None
        product_id (int | None): ID товара или None
        order_id (int | None): ID заказа или None
        sizes (tuple[int], optional): Распределение кнопок

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(
            InlineKeyboardButton(
                text="Оплатить",
                callback_data=MenuCallBack(
                    level=6,
                    menu_name="payment",
                    product_id=product_id,
                    order_id=order_id,
                    page=page,
                ).pack(),
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                text="Удалить",
                callback_data=MenuCallBack(
                    level=7,
                    menu_name="delete",
                    product_id=product_id,
                    page=page,
                    order_id=order_id,
                ).pack(),
            )
        )
        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in cast(Dict[Any, Any], pagination_btns).items():
            if menu_name == "next":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page + 1
                        ).pack(),
                    )
                )
            elif menu_name == "previous":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page - 1
                        ).pack(),
                    )
                )

        keyboard.row(*row)

        row2 = [
            InlineKeyboardButton(
                text="На главную 🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            ),
        ]
        return keyboard.row(*row2).as_markup()
    else:
        keyboard.add(
            InlineKeyboardButton(
                text="На главную 🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            )
        )

        return keyboard.adjust(*sizes).as_markup()


def get_callback_btns(
    *, btns: dict[str, str], sizes: tuple[int] = (2,)
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает кастомную клавиатуру из переданных кнопок

    Args:
        btns (dict[str, str]): Словарь
        sizes (tuple[int], optional): Распределение кнопок

    Returns:
        InlineKeyboardMarkup: Готовая клавиатура с заданными кнопками
    """
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
