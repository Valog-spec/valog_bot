from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_banner, get_all_orders, get_order_by_order_id, delete_order
from kbds.inline.admin.inline_admin import get_orders_keyboard, get_admin_keyboard, get_order_actions_keyboard, \
    get_statuses_keyboard, get_confirm_delete_keyboard


async def main(session):
    banner = await orm_get_banner(session, "main")
    kbds = get_admin_keyboard()

    if banner.image:
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
    else:
        image = None

    return image, kbds


async def orders_list(session):
    banner = await orm_get_banner(session, "orders")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    orders = await get_all_orders(session)

    kbds = get_orders_keyboard(orders)

    return image, kbds


async def view_order(order_id, session):
    banner = await orm_get_banner(session, "orders")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_order_actions_keyboard(order_id)
    return image, kbds


async def change_status(session, order_id, action, status):
    order = await get_order_by_order_id(order_id, session)
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

    banner = await orm_get_banner(session, "orders")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds

async def order_delete(session, order_id):

    kbds = get_confirm_delete_keyboard(order_id)

    banner = await orm_get_banner(session, "orders")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds

async def confirm_delete(session, order_id):

    banner = await orm_get_banner(session, "orders")
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    await delete_order(session, order_id)
    orders = await get_all_orders(session)
    kbds = get_orders_keyboard(orders)

    return image, kbds


async def get_admin_menu_content(
        session: AsyncSession,
        action: str | None = None,
        order_id: int | None = None,
        status: str | None = None,
):
    if action == "main":
        return await main(session)
    elif action == "list_orders":
        return await orders_list(session)
    elif action == "view":
        return await view_order(order_id, session)
    elif action == "edit_status":
        return await change_status(session, order_id, action, status)
    elif action == "delete":
        return await order_delete(session, order_id)
    elif action == "confirm_delete":
        return await confirm_delete(session, order_id)
