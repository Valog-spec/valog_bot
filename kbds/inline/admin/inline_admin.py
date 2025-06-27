from aiogram.types import  InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardBuilder


class OrderCallback(CallbackData, prefix="order"):
    action: str
    order_id: int
    status: Optional[str] = None


class AdminAction(CallbackData, prefix="admin"):
    action: str


def get_admin_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Cписок заказов',
                                      callback_data=AdminAction(action='list_orders').pack()))
    keyboard.add(InlineKeyboardButton(text="Добавить товар",
                                      callback_data=AdminAction(action="add_product").pack()))
    keyboard.add(InlineKeyboardButton(text="Ассортимент",
                                      callback_data=AdminAction(action="catalog").pack()))
    keyboard.add(InlineKeyboardButton(text="Добавить/Изменить баннер",
                                      callback_data=AdminAction(action="banner").pack()))

    return keyboard.adjust(2).as_markup()


def get_orders_keyboard(orders: list):
    keyboard = InlineKeyboardBuilder()
    for order in orders:
        keyboard.add(InlineKeyboardButton(
            text=f"Заказ #{order.id} ({order.status})",
            callback_data=OrderCallback(
                action="view",
                order_id=order.id
            ).pack()))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data=AdminAction(action="main").pack()))

    return keyboard.adjust(2).as_markup()


def get_order_actions_keyboard(order_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✏️ Изменить статус",
        callback_data=OrderCallback(
            action="edit_status",
            order_id=order_id
        ).pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text="❌ Удалить",
        callback_data=OrderCallback(
            action="delete",
            order_id=order_id
        ).pack()
    ))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data=AdminAction(action="list_orders").pack()))
    return keyboard.adjust(2).as_markup()


def get_statuses_keyboard(order_id: int):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(
        text="🔄 В обработке",
        callback_data=OrderCallback(
            action="edit_status",
            order_id=order_id,
            status="processing"
        ).pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text="🚚 Отправлен",
        callback_data=OrderCallback(
            action="edit_status",
            order_id=order_id,
            status="shipped"
        ).pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text="✅ Доставлен",
        callback_data=OrderCallback(
            action="edit_status",
            order_id=order_id,
            status="delivered"
        ).pack()
    ))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data=AdminAction(action="list_orders").pack()))

    return keyboard.adjust(2).as_markup()


def get_confirm_delete_keyboard(order_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✅ Да, удалить",
        callback_data=OrderCallback(
            action="confirm_delete",
            order_id=order_id
        ).pack()
    ))

    keyboard.add(InlineKeyboardButton(
        text="❌ Нет, отмена",
        callback_data=AdminAction(action="list_orders").pack()
    ))
    return keyboard.adjust(2).as_markup()
