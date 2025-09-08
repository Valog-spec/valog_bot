from typing import Optional, Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OrderCallback(CallbackData, prefix="order"):
    """
    Класс для обработки callback-действий, связанных с заказами

    Attributes:
       action (str): Действие, которое нужно выполнить с заказом
       order_id (int): Уникальный идентификатор заказа
       status (Optional[str]): Новый статус заказа (используется при изменении статуса)
    """

    action: str
    order_id: int
    status: Optional[str] = None


class AdminAction(CallbackData, prefix="admin"):
    """
    Класс для обработки callback-действий администратора

    Наследуется от CallbackData и использует префикс 'admin' для идентификации

    Attributes:
        action (str): Действие администратора
    """

    action: str
    user_id: Optional[int] = None


def get_admin_keyboard() -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру с основными действиями администратора

    Returns:
       InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Cписок заказов",
            callback_data=AdminAction(action="list_orders").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Добавить товар",
            callback_data=AdminAction(action="add_product").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Ассортимент", callback_data=AdminAction(action="catalog").pack()
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Добавить/Изменить баннер",
            callback_data=AdminAction(action="banner").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Вопросы пользователей",
            callback_data=AdminAction(action="support").pack(),
        )
    )

    return keyboard.adjust(2).as_markup()


def get_orders_keyboard(orders: Sequence) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру со списком заказов для администратора

    Args:
        orders (Sequence): Последовательность заказов (обычно список)

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    for order in orders:
        keyboard.add(
            InlineKeyboardButton(
                text=f"Заказ #{order.id} ({order.status})",
                callback_data=OrderCallback(action="view", order_id=order.id).pack(),
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=AdminAction(action="main").pack()
        )
    )

    return keyboard.adjust(2).as_markup()


def get_order_actions_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру с действиями для конкретного заказа

    Args:
        order_id (int): ID заказа для которого создаются действия

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✏️ Изменить статус",
            callback_data=OrderCallback(action="edit_status", order_id=order_id).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="❌ Удалить",
            callback_data=OrderCallback(action="delete", order_id=order_id).pack(),
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=AdminAction(action="list_orders").pack()
        )
    )
    return keyboard.adjust(2).as_markup()


def get_statuses_keyboard(order_id: int) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает клавиатуру с возможными статусами для заказа

    Args:
        order_id (int): ID заказа для которого меняется статус

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="🔄 В обработке",
            callback_data=OrderCallback(
                action="edit_status", order_id=order_id, status="processing"
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🚚 Отправлен",
            callback_data=OrderCallback(
                action="edit_status", order_id=order_id, status="shipped"
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Доставлен",
            callback_data=OrderCallback(
                action="edit_status", order_id=order_id, status="delivered"
            ).pack(),
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=AdminAction(action="list_orders").pack()
        )
    )

    return keyboard.adjust(2).as_markup()


def get_confirm_delete_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
     Создает клавиатуру подтверждения удаления заказа

    Args:
        order_id (int): ID заказа который будет удален

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=OrderCallback(
                action="confirm_delete", order_id=order_id
            ).pack(),
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ Нет, отмена",
            callback_data=AdminAction(action="list_orders").pack(),
        )
    )
    return keyboard.adjust(2).as_markup()


def get_support_keyboard(users):
    keyboard = InlineKeyboardBuilder()
    for i in users:
        keyboard.add(
            InlineKeyboardButton(
                text=f"Вопросы пользователя {i}",
                callback_data=AdminAction(action="view_questions", user_id=i).pack(),
            )
        )
    keyboard.add(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=AdminAction(action="main").pack()
        )
    )

    return keyboard.adjust(1, 1).as_markup()


def get_support_keyboard_by_user_support(user_support):
    keyboard = InlineKeyboardBuilder()
    for i in user_support:
        print(i.content)
        keyboard.add(
            InlineKeyboardButton(
                text=f"Вопрос пользователя: {i.content}\nНомер пользователя: {i.phone}",
                callback_data=AdminAction(
                    action="view_questions", user_id=i.user_id
                ).pack(),
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=AdminAction(action="main").pack()
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Удалить",
            callback_data=AdminAction(
                action="view_questions", user_id=i.user_id
            ).pack(),
        )
    )

    return keyboard.adjust(1, 2).as_markup()
