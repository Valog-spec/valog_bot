from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from bot_instance import bot
from database.models import Banner, Cart, Category, Product, User, Order


############### Работа с баннерами (информационными страницами) ###############

async def orm_add_banner_description(session: AsyncSession, data: dict):
    #Добавляем новый или изменяем существующий по именам
    #пунктов меню: main, about, cart, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()]) 
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


############################ Категории ######################################

async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories]) 
    await session.commit()

############ Админка: добавить/изменить/удалить товар ########################

async def orm_add_product(session: AsyncSession, data: dict):
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_products(session: AsyncSession, category_id):
    query = select(Product).where(Product.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    # cart_items = await session.scalars(select(Cart).where(Cart.user_id == user_id))
    # for item in cart_items:
    #     await session.delete(item)
    # await session.commit()
    return result.scalar()


async def orm_update_product(session: AsyncSession, product_id: int, data):
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


async def orm_delete_product(session: AsyncSession, product_id: int):
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()

##################### Добавляем юзера в БД #####################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name)
        )
        await session.commit()


######################## Работа с корзинами #######################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()



async def orm_get_user_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False

async def orm_get_cart(session:AsyncSession, user_id, product_id):
    query = select(Cart).filter(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    return cart.scalar()

async def orm_delete_order_in_cart(session:AsyncSession, order):
    product_id = order.user.cart.product.id
    await session.delete()


# Заказы

async def orm_create_order(user_id, data, session: AsyncSession):
    cart = await orm_get_cart(session, user_id, data["product_id"])
    product = await orm_get_product(session, data["product_id"])

    order = Order(user_id=user_id, full_name=data["full_name"],
                  status="В обработке",
                  address=data["address"],
                  phone=data["phone"],
                  product_id=data["product_id"],
                  total_price=cart.quantity * product.price)
    session.add(order)
    # cart_items = await session.scalars(select(Cart).where(Cart.user_id == user_id))
    # for item in cart_items:
    #     await session.delete(item)
    await session.commit()
    # [7549979647, 1677148093]
    try:
        await bot.send_message(
            chat_id=1677148093,
            text=f"""🛒<b>Новый заказ #{order.id}</b>
                    👤 Клиент: {order.full_name}
                    📞 Телефон: {order.phone}
                    📍 Адрес: {order.address}
                    💰 Сумма: {order.total_price} руб.
                    🕒 Время: {order.created}""",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление админу {1677148093}: {e}")


async def get_orders(session:AsyncSession, user_id):
    # query = select(Order).where(Order.user_id == user_id).options(joinedload(Order.user).options(joinedload(User.cart)))
    # result = await session.execute(query)
    # return result.unique().scalars().all()

    query = select(Order).where(Order.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()

async def get_order_by_order_id(order_id, session:AsyncSession):
    order = await session.get(Order, order_id)
    return order


async def get_all_orders(session:AsyncSession):
    # query = select(Order).options(joinedload(Order.user).options(joinedload(User.cart)))
    query = select(Order)
    result = await session.execute(query)
    return result.scalars().all()

async def delete_order(session:AsyncSession, order_id):
    order = await get_order_by_order_id(order_id, session)
    await session.delete(order)
    await session.commit()

async def change_order(session:AsyncSession, order_id):
    order = await get_order_by_order_id(order_id, session)
    order.paid = True
    await session.commit()



# payment

async def orm_get_total_price(session, order_id):
    order = await get_order_by_order_id(order_id, session)
    return order.total_price









