from aiogram import F, types, Router
from aiogram.filters import CommandStart, StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot_instance import bot
from database.orm_query import (
    orm_add_to_cart,
    orm_add_user, orm_get_total_price, change_order,
)
from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import MenuCallBack, get_callback_btns
from kbds.reply import get_keyboard, contact

from payments.ukassa import create_payment

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))

@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")


    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    user = callback.from_user
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    await orm_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer("Товар добавлен в корзину.")

class AddOrder(StatesGroup):
    full_name = State()
    address = State()
    phone = State()

    texts = {
        "AddOrder:full_name": "Введите ФИО заново:",
        "AddOrder:address": "Введите адрес заново:",
        "AddOrder:phone": "Введите номер телефона заново:",

    }

@user_private_router.callback_query(StateFilter(None), MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession, state:FSMContext):
    if callback_data.menu_name == "add_to_cart":
        await add_to_cart(callback, callback_data, session)
        return
    elif callback_data.menu_name == "order":
        await callback.message.answer("Введите ФИО: ")
        await state.update_data(product_id=callback_data.product_id)
        await state.set_state(AddOrder.full_name)
        await callback.answer()
        return
    elif callback_data.menu_name == "payment":
        price = await orm_get_total_price(session, callback_data.order_id)
        payment = await create_payment(
            amount=price,
            description=f"Оплата заказа #{callback_data.order_id}"
        )
        await (callback.message.answer_invoice(
            title="Тестовый платеж",
            description="Описание товара",
            provider_token="381764678:TEST:129074",
            currency="RUB",
            prices=[LabeledPrice(label="Товар", amount=price * 100)],
            payload=f"order_{callback_data.order_id}",
            start_parameter=payment.id
        ))
        return

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
        order_id=callback_data.order_id
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


@user_private_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
    await pre_checkout_query.bot.send_message(
        chat_id=pre_checkout_query.from_user.id,
        text="Спасибо за оплату! Проверяем платеж..."
    )

@user_private_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message, session: AsyncSession):
    payment = message.successful_payment
    order_id = payment.invoice_payload.split('_')[1]
    await change_order(session, int(order_id))
    await message.answer(
        "✅ Платеж получен!\n"
        f"ID: {payment.telegram_payment_charge_id}\n"
        f"Сумма: {payment.total_amount / 100} {payment.currency}\n"
        f"Товар: {payment.invoice_payload}"
    )

# Заказ

@user_private_router.message(StateFilter("*"), Command("назад2"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "назад2")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddOrder.full_name:
        await message.answer(
            'Предидущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    for step in AddOrder.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n {AddOrder.texts[previous.state]}"
            )
            return
        previous = step

@user_private_router.message(StateFilter("*"), Command("отмена2"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "отмена2")
async def cancel_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer("Действия отменены", reply_markup=reply_markup)

@user_private_router.message(AddOrder.full_name, F.text)
async def fio_process(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Теперь введите адрес доставки:")
    await state.set_state(AddOrder.address)

@user_private_router.message(AddOrder.full_name)
async def start_order_2(message: types.Message, state: FSMContext):
    await message.answer("Введите еще раз ваше ФИО: ")


@user_private_router.message(AddOrder.address, F.text)
async def address_process(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Отпроавить номер телефона", reply_markup=contact())
    await state.set_state(AddOrder.phone)

@user_private_router.message(AddOrder.address)
async def address_process_2(message: types.Message, state: FSMContext):
    await message.answer("Повторите адрес доставки:")

@user_private_router.message(AddOrder.phone, or_f(F.contact, F.text))
async def phone_process(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.contact:
        await state.update_data(phone=message.contact.phone_number)
    else:
        await state.update_data(phone=message.text)
    data = await state.get_data()
    media, reply_markup = await get_menu_content(
        session,
        level=4,
        menu_name="main",
        user_id=message.from_user.id,
        data = data)

    await message.answer("Заказ в обработке", reply_markup=reply_markup)

    await state.clear()


@user_private_router.message(AddOrder.phone)
async def phone_process_2(message: types.Message, state: FSMContext):
    contact_btn = get_keyboard("Отправить контакт", request_contact=True)
    await message.answer("Отпроавьте номер телефона, либо введите его вручную", reply_markup=contact_btn)



    




