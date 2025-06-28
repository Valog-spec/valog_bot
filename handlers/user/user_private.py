from typing import cast

from aiogram import F, Router, types
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandStart, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    change_order,
    orm_add_to_cart,
    orm_add_user,
    orm_get_total_price,
)
from filters.chat_types import ChatTypeFilter
from handlers.user.user_menu_processing import get_menu_content
from kbds.inline.user.inline import MenuCallBack
from kbds.reply.reply import contact, get_keyboard
from logger.logger_helper import get_logger
from payments.ukassa import create_payment

logger = get_logger("logger.user_private")
user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession) -> None:
    """
    Обработчик команды /start. Инициализирует главное меню для пользователя

    Args:
       message (types.Message): Входящее сообщение с командой
       session (AsyncSession): Асинхронная сессия для работы с БД
    """
    logger.info("Обработка /start. User ID: %d", message.from_user.id)
    logger.debug("Загрузка главного меню (level=0)")
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(
        media.media, caption=media.caption, reply_markup=reply_markup
    )
    logger.info("Главное меню успешно отправлено пользователю")


async def add_to_cart(
    callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession
) -> None:
    """
    Добавляет товар в корзину пользователя и создает пользователя если его нет в БД

    Args:
        callback (types.CallbackQuery): Callback запрос от кнопки
        callback_data (MenuCallBack): Данные callback
        session (AsyncSession): Асинхронная сессия для работы с БД
    """
    user = callback.from_user

    logger.info("Добавление товара в корзину. User: %d", user.id)
    logger.debug("Проверка/создание пользователя %d", user.id)
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    logger.debug("Добавление товара в корзину %d", user.id)
    assert callback_data.product_id is not None
    await orm_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer("Товар добавлен в корзину.")
    logger.info("Товар успешно добавлен в корзину %d", user.id)


class AddOrder(StatesGroup):
    """
    Группа состояний для оформления заказа

    Атрибуты:
        texts (dict): Сообщения для повторного ввода при ошибках валидации.
    """

    full_name = State()
    address = State()
    phone = State()

    texts = {
        "AddOrder:full_name": "Введите ФИО заново:",
        "AddOrder:address": "Введите адрес заново:",
        "AddOrder:phone": "Введите номер телефона заново:",
    }


@user_private_router.callback_query(StateFilter(None), MenuCallBack.filter())
async def user_menu(
    callback: types.CallbackQuery,
    callback_data: MenuCallBack,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Обработчик callback-запросов для пользовательского меню

    Args:
        callback (types.CallbackQuery): Callback запрос
        callback_data (MenuCallBack): Данные callback
        session (AsyncSession): Асинхронная сессия БД
        state (FSMContext): Контекст машины состояний
    """

    logger.info("Обработка callback. User: %d", callback.from_user.id)
    if callback_data.menu_name == "add_to_cart":
        logger.debug("Добавление товара в корзину")
        await add_to_cart(callback, callback_data, session)
        return
    elif callback_data.menu_name == "order":
        logger.info("Начало оформления заказа для товара")
        await callback.message.answer("Введите ФИО: ")
        await state.update_data(product_id=callback_data.product_id)
        await state.set_state(AddOrder.full_name)
        await callback.answer()
        return
    elif callback_data.menu_name == "payment":
        logger.info("Начало оплаты заказа")
        price = await orm_get_total_price(session, cast(int, callback_data.order_id))
        payment = await create_payment(
            amount=price, description=f"Оплата заказа #{callback_data.order_id}"
        )
        logger.info("Создана платежная сессия: %d", payment.id)

        await callback.message.answer_invoice(
            title="Тестовый платеж",
            description="Описание товара",
            provider_token="381764678:TEST:129074",
            currency="RUB",
            prices=[LabeledPrice(label="Товар", amount=round(price * 100))],
            payload=f"order_{callback_data.order_id}",
            start_parameter=payment.id,
        )
        return

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
        order_id=callback_data.order_id,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
    logger.debug("Меню успешно обновлено")


@user_private_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    """
    Обработчик предварительного подтверждения платежа

    Args:
        pre_checkout_query (PreCheckoutQuery): Запрос подтверждения платежа
    """
    await pre_checkout_query.answer(ok=True)
    logger.debug("Pre-checkout подтвержден для %d", pre_checkout_query.id)
    await pre_checkout_query.bot.send_message(
        chat_id=pre_checkout_query.from_user.id,
        text="Спасибо за оплату! Проверяем платеж...",
    )
    logger.info(
        "Отправлено подтверждение пользователю %d", pre_checkout_query.from_user.id
    )


@user_private_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(
    message: types.Message, session: AsyncSession
) -> None:
    """
     Обработчик успешного платежа

    Args:
        message (types.Message): Сообщение с данными платежа
        session (AsyncSession): Асинхронная сессия БД
    """
    payment = message.successful_payment
    order_id = payment.invoice_payload.split("_")[1]
    logger.debug("Обработка заказа %d", order_id)
    await change_order(session, int(order_id))
    logger.info("Статус заказа %d обновлен на 'оплачен'", order_id)
    await message.answer(
        "✅ Платеж получен!\n"
        f"ID: {payment.telegram_payment_charge_id}\n"
        f"Сумма: {payment.total_amount / 100} {payment.currency}\n"
        f"Товар: {payment.invoice_payload}"
    )
    logger.debug("Чек отправлен пользователю %d", message.from_user.id)


@user_private_router.message(StateFilter("*"), Command("назад2"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "назад2")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды 'назад2'. Возвращает пользователя на предыдущий шаг в машине состояний

    Args:
       message (types.Message): Входящее сообщение от пользователя
       state (FSMContext): Контекст состояния FSM
    """
    current_state = await state.get_state()
    logger.info(
        "Пользователь %d запросил возврат на предыдущий шаг. Текущее состояние: %s",
        message.from_user.id,
        current_state,
    )

    if current_state == AddOrder.full_name:
        logger.info(
            "Пользователь %d пытается вернуться назад из начального состояния",
            message.from_user.id,
        )
        await message.answer(
            'Предидущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    for step in AddOrder.__all_states__:
        if step.state == current_state:
            assert previous is not None
            await state.set_state(previous)
            logger.info(
                "Пользователь %d возвращен к предыдущему шагу: %s",
                message.from_user.id,
                previous.state,
            )
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n {AddOrder.texts[cast(str, previous.state)]}"
            )
            return
        previous = step


@user_private_router.message(StateFilter("*"), Command("отмена2"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "отмена2")
async def cancel_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик команды 'отмена2'. Сбрасывает текущее состояние и возвращает в главное меню

    Args:
        message (types.Message): Входящее сообщение
        state (FSMContext): Контекст состояния FSM
        session (AsyncSession): Асинхронная сессия БД

    """
    current_state = await state.get_state()
    if current_state is None:
        logger.info(
            "Пользователь %d попытался отменить действие, но состояние уже пустое",
            message.from_user.id,
        )
        return
    logger.info(
        "Пользователь %d отменил действие. Текущее состояние очищено: %s",
        message.from_user.id,
        current_state,
    )
    await state.clear()
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer("Действия отменены", reply_markup=reply_markup)


@user_private_router.message(AddOrder.full_name, F.text)
async def fio_process(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод ФИО при оформлении заказа
    """
    logger.info("Пользователь %d ввел ФИО: %s", message.from_user.id, message.text)
    await state.update_data(full_name=message.text)
    await message.answer("Теперь введите адрес доставки:")
    await state.set_state(AddOrder.address)


@user_private_router.message(AddOrder.full_name)
async def start_order_2(message: types.Message) -> None:
    """
    Повторный запрос ФИО при некорректном вводе
    """
    await message.answer("Введите еще раз ваше ФИО: ")


@user_private_router.message(AddOrder.address, F.text)
async def address_process(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод адреса доставки
    """
    logger.info("Пользователь %d ввел адрес: %s", message.from_user.id, message.text)
    await state.update_data(address=message.text)
    await message.answer("Отпроавить номер телефона", reply_markup=contact())
    await state.set_state(AddOrder.phone)


@user_private_router.message(AddOrder.address)
async def address_process_2(message: types.Message) -> None:
    """
    Повторный запрос адреса при некорректном вводе
    """
    logger.info("Пользователь ввел некорректный адрес")
    await message.answer("Повторите адрес доставки:")


@user_private_router.message(AddOrder.phone, or_f(F.contact, F.text))
async def phone_process(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    """
    Завершает заказ после получения телефона
    """
    if message.contact:
        logger.info(
            "Пользователь %d отправил контакт: %d",
            message.from_user.id,
            message.contact.phone_number,
        )
        await state.update_data(phone=message.contact.phone_number)
    else:
        logger.info(
            "Пользователь %d ввел телефон вручную: %s",
            message.from_user.id,
            message.text,
        )
        await state.update_data(phone=message.text)
        await message.answer(text="Номер записан!", reply_markup=ReplyKeyboardRemove())
    data = await state.get_data()
    media, reply_markup = await get_menu_content(
        session, level=4, menu_name="main", user_id=message.from_user.id, data=data
    )

    await message.answer("Заказ в обработке", reply_markup=reply_markup)
    logger.info(
        "Завершение оформления заказа для пользователя %d. Данные: %s",
        message.from_user.id,
        data,
    )
    await state.clear()


@user_private_router.message(AddOrder.phone)
async def phone_process_2(message: types.Message) -> None:
    """
    Повторный запрос телефона с клавиатурой контакта
    """
    logger.info("Пользователь ввел некорректный номер телефона")

    contact_btn = get_keyboard("Отправить контакт", request_contact=True)
    await message.answer(
        "Отпроавьте номер телефона, либо введите его вручную", reply_markup=contact_btn
    )
