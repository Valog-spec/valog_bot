from typing import List, Optional, cast

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InaccessibleMessage, InputMediaPhoto, PhotoSize
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from database.orm_query import (
    orm_add_product,
    orm_change_banner_image,
    orm_delete_product,
    orm_get_categories,
    orm_get_info_pages,
    orm_get_product,
    orm_get_products,
    orm_update_product,
)
from filters.chat_types import ChatTypeFilter, IsAdmin
from handlers.admin.admin_menu_processing import get_admin_menu_content
from kbds.inline.admin.inline_admin import (
    AdminAction,
    OrderCallback,
    get_admin_keyboard,
)
from kbds.inline.user.inline import get_callback_btns
from logger.logger_helper import get_logger

logger = get_logger("logger.admin_private")

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


@admin_router.message(Command("admin"))
async def start(message: types.Message, session: AsyncSession) -> None:
    """
    Обработчик команды /admin для отображения меню админа

    Args:
        message (types.Message): Входящее сообщение от пользователя
        session (AsyncSession): Асинхронная сессия SQLAlchemy
    """
    logger.info("Администратор %d запросил меню", message.from_user.id)
    media, reply_markup = await get_admin_menu_content(session, action="main")
    if not media:
        logger.debug(
            "Отправка текстового меню для администратора %d", message.from_user.id
        )
        await message.answer("Что хотите сделать?", reply_markup=reply_markup)
    else:
        logger.debug("Отправка меню для администратора %d", message.from_user.id)
        await message.answer_photo(
            media.media, caption=media.caption, reply_markup=reply_markup
        )
    logger.info(
        "Меню администратора успешно отправлено пользователю %d", message.from_user.id
    )


@admin_router.callback_query(AdminAction.filter())
async def list_orders(
    callback: types.CallbackQuery,
    callback_data: AdminAction,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Обработчик callback-запросов для действий администратора

    Args:
        callback (types.CallbackQuery): Входящий callback запрос
        callback_data (AdminAction): Данные callback с указанием действия
        session (AsyncSession): Асинхронная сессия SQLAlchemy
        state (FSMContext): Контекст машины состояний
    """
    if callback_data.action == "catalog":
        logger.info("Админ %d запросил каталог", callback.from_user.id)
        await admin_features(callback.message, session)
        return
    elif callback_data.action == "add_product":
        logger.info("Админ %dначал добавление товара", callback.from_user.id)
        await callback.message.answer(
            "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(AddProduct.name)
        await callback.answer()
        return
    elif callback_data.action == "banner":
        logger.info("Админ %d начал добавление баннера", callback.from_user.id)
        pages_names = [page.name for page in await orm_get_info_pages(session)]
        await callback.message.answer(
            f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                                 \n{', '.join(pages_names)}"
        )
        await state.set_state(AddBanner.image)
        return
    logger.debug(
        "Админ %d запросил меню действия: %s",
        callback.from_user.id,
        callback_data.action,
    )
    media, reply_markup = await get_admin_menu_content(
        session,
        action=callback_data.action,
    )

    await callback.message.edit_media(
        media=cast(InputMediaPhoto, media), reply_markup=reply_markup
    )
    logger.debug("Меню для действия %s успешно обновлено", callback_data.action)
    await callback.answer()


@admin_router.callback_query(OrderCallback.filter())
async def view_order(
    callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession
) -> None:
    """
     Обработчик callback-запроса для работы с заказами в админ-панели

    Args:
        callback (CallbackQuery): Входящий callback-запрос
        callback_data (OrderCallback): Данные callback'а:
        session (AsyncSession): Асинхронная сессия SQLAlchemy

    """
    logger.info(
        "Обработка callback по заказу. Пользователь: %d Действие: %s, Заказ: %d, Статус: %s",
        callback.from_user.id,
        callback_data.action,
        callback_data.order_id,
        callback_data.status,
    )
    media, reply_markup = await get_admin_menu_content(
        session,
        action=callback_data.action,
        order_id=callback_data.order_id,
        status=callback_data.status,
    )

    await callback.message.edit_media(
        media=cast(InputMediaPhoto, media), reply_markup=reply_markup
    )
    await callback.answer()
    logger.info(
        "Callback по заказу %d обработан, Пользователь: %d",
        callback_data.order_id,
        callback.from_user.id,
    )


async def admin_features(
    message: types.Message | InaccessibleMessage | None, session: AsyncSession
) -> None:
    """
    Отображает интерфейс выбора категорий для администратора

    Args:
        message (types.Message): Входящее сообщение от администратора
        session (AsyncSession): Асинхронная сессия SQLAlchemy
    """
    logger.info("Администратор %d запросил список категорий", message.from_user.id)
    categories = await orm_get_categories(session)
    btns = {category.name: f"category_{category.id}" for category in categories}
    await message.answer(
        "Выберите категорию", reply_markup=get_callback_btns(btns=btns)
    )
    logger.info(
        "Список категорий успешно отправлен администратору %d, ", message.from_user.id
    )


@admin_router.callback_query(F.data.startswith("category_"))
async def starring_at_product(
    callback: types.CallbackQuery, session: AsyncSession
) -> None:
    """
    Обработчик выбора категории товаров в админ-панели

    Args:
        callback (types.CallbackQuery): Callback запрос с данными выбранной категории
        session (AsyncSession): Асинхронная сессия SQLAlchemy
    """

    logger.info(
        "Админ %d выбрал категорию. Callback data: %s",
        callback.from_user.id,
        callback.data,
    )
    category_id = callback.data.split("_")[-1]
    logger.debug("Извлечен ID категории: %d", category_id)
    for product in await orm_get_products(session, int(category_id)):
        logger.debug("Отправка товара ID %d. Название: %s", product.id, product.name)
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                },
                sizes=(2,),
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫")
    logger.info(
        "Завершена обработка категории %d для админа %d",
        category_id,
        callback.from_user.id,
    )


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(
    callback: types.CallbackQuery, session: AsyncSession
) -> None:
    """
    Обработчик callback для удаления товара

    Args:
        callback (types.CallbackQuery): Входящий callback запрос
        session (AsyncSession): Асинхронная сессия SQLAlchemy
    """
    logger.info(
        "Начало удаления товара. Пользователь: %d, Callback data: %s",
        callback.from_user.id,
        callback.data,
    )
    product_id = callback.data.split("_")[-1]

    logger.debug("Извлечен ID товара для удаления: %d", product_id)
    await orm_delete_product(session, int(product_id))
    logger.info(
        "Товар %d успешно удален из БД. Удалил: %d", product_id, callback.from_user.id
    )

    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


class AddBanner(StatesGroup):
    """
    Группа состояние для процесса добавления нового баннера в систему
    """

    image = State()


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик для добавления/изменения баннера страницы


    Args:
        message: Объект сообщения от пользователя с фото и подписью
        state: Текущее состояние FSM
        session: Асинхронная сессия SQLAlchemy
    """
    photos = cast(List[PhotoSize], message.photo)
    image_id = photos[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    logger.info("Попытка добавления баннера для страницы: %s", for_page)
    if for_page not in pages_names:
        await message.answer(
            f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}"
        )
        return
    await orm_change_banner_image(
        session,
        for_page,
        image_id,
    )
    logger.info("Баннер для страницы %s успешно обновлен", for_page)
    await message.answer("Баннер добавлен/изменен.", reply_markup=get_admin_keyboard())
    await state.clear()


@admin_router.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для случая, когда пользователь не отправил фото

    Параметры:
        message: Объект сообщения от пользователя
        state: Текущее состояние FSM
    """
    logger.warning(
        "Пользователь отправил сообщение без фото в процессе добавления баннера"
    )
    await message.answer("Отправьте фото баннера или отмена")


class AddProduct(StatesGroup):
    """
    Группа состояний для добавления или изменения товара

    Args:
        name (State): Состояние для ввода названия товара.
        description (State): Состояние для ввода описания товара.
        category (State): Состояние для выбора категории товара.
        price (State): Состояние для ввода цены товара.
        image (State): Состояние для загрузки изображения товара.
    """

    name = State()
    description = State()
    category = State()
    price = State()
    image = State()

    product_for_change: Optional[Product] = None

    texts = {
        "AddProduct:name": "Введите название заново:",
        "AddProduct:description": "Введите описание заново:",
        "AddProduct:category": "Выберите категорию  заново ⬆️",
        "AddProduct:price": "Введите стоимость заново:",
        "AddProduct:image": "Этот стейт последний, поэтому...",
    }


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик callback-запроса для изменения существующего товара

    Args:
        callback (types.CallbackQuery): Callback запрос от кнопки изменения товара
        state (FSMContext): Контекст машины состояний
        session (AsyncSession): Асинхронная сессия для работы с БД
    """
    logger.info("Получен запрос на изменение товара. Callback data: %s", callback.data)
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))
    logger.info("Товар для изменения получен из БД. ID: %d", product_id)

    AddProduct.product_for_change = product_for_change
    logger.info(
        "Установлен товар для изменения. ID: %d, Название: %s",
        product_id,
        product_for_change.name,
    )

    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    logger.info(
        "Начат процесс изменения товара. ID: %d. Ожидается ввод названия", product_id
    )
    await state.set_state(AddProduct.name)


@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик отмены текущего действия и сброса состояния

    Args:
        message (types.Message): Входящее сообщение с командой отмены
        state (FSMContext): Контекст машины состояний
    """
    logger.info("Получена команда отмены от пользователя %d", message.from_user.id)

    current_state = await state.get_state()
    if current_state is None:
        logger.debug("Нет активного состояния - ничего не делаем")
        return
    if AddProduct.product_for_change:
        logger.info("Сброс товара для изменения")
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=get_admin_keyboard())
    logger.info("Пользователю отправлено подтверждение отмены")


@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды 'назад' для возврата к предыдущему шагу в машине состояний

    Параметры:
       message (types.Message): Входящее сообщение с командой
       state (FSMContext): Контекст машины состояний
    """
    logger.info("Получена команда 'назад' от пользователя %d", message.from_user.id)
    current_state = await state.get_state()

    if current_state == AddProduct.name:
        logger.info("Попытка вернуться назад из начального состояния (name)")
        await message.answer(
            'Предидущего шага нет, или введите название товара или напишите "отмена"'
        )

        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            assert previous is not None
            logger.info("Найден текущий шаг в цепочке состояний: %s", current_state)
            await state.set_state(previous)
            logger.info("Успешный возврат на предыдущий шаг: %s", previous.state)
            await message.answer(
                "Ок, вы вернулись к прошлому шагу \n %s",
                AddProduct.texts[cast(str, previous.state)],
            )
            return
        previous = step


@admin_router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик состояния ввода названия товара
    Args:
        message (types.Message): Сообщение с названием товара
        state (FSMContext): Контекст машины состояний
    """
    logger.info(
        "Получено название товара: '%s' | Режим изменения: %s",
        message.text,
        bool(AddProduct.product_for_change),
    )
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(name=AddProduct.product_for_change.name)
        logger.info("Использовано старое название товара")
    else:
        if 4 >= len(cast(str, message.text)) >= 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\nили быть менее 5ти символов. \n Введите заново"
            )
            logger.warning(
                "Некорректная длина названия: %d символов", len(cast(str, message.text))
            )
            return
        await state.update_data(name=message.text)
        logger.info("Сохранено новое название товара: '%s'", message.text)
    await message.answer("Введите описание товара")
    logger.info("Переход к состоянию ввода описания товара")
    await state.set_state(AddProduct.description)


@admin_router.message(AddProduct.name)
async def add_name2(message: types.Message) -> None:
    """
    Обработчик невалидного ввода названия товара

    Args:
        message (types.Message): Сообщение с невалидными данными
    """
    logger.warning(
        "Получен невалидный ввод названия товара, User ID: %d", message.from_user.id
    )
    await message.answer("Вы ввели не допустимые данные, введите текст названия товара")


@admin_router.message(AddProduct.description, F.text)
async def add_description(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик состояния ввода описания товара

    Args:
        message (types.Message): Сообщение с описанием товара
        state (FSMContext): Контекст машины состояний
        session (AsyncSession): Асинхронная сессия для работы с БД
    """

    logger.info(
        "Начало обработки описания товара. Режим: %s",
        "изменение" if AddProduct.product_for_change else "добавление",
    )
    if message.text == "." and AddProduct.product_for_change:
        logger.info("Использовано старое описание товара")
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        if 4 >= len(cast(str, message.text)):
            logger.warning("Слишком короткое описание")
            await message.answer("Слишком короткое описание. \n Введите заново")
            return
        logger.info("Сохранено новое описание товара. Длина")
        await state.update_data(description=message.text)

    logger.debug("Загрузка категорий из БД")
    categories = await orm_get_categories(session)
    btns = {category.name: str(category.id) for category in categories}
    await message.answer(
        "Выберите категорию", reply_markup=get_callback_btns(btns=btns)
    )
    logger.debug("Отправлено сообщение с выбором категории")
    await state.set_state(AddProduct.category)
    logger.info("Переход к состоянию выбора категории")


@admin_router.message(AddProduct.description)
async def add_description2(message: types.Message):
    """
    Обработчик невалидного ввода описания товара

    Args:
        message (types.Message): Сообщение с невалидными данными
        state (FSMContext): Контекст машины состояний

    """
    logger.warning("Невалидный ввод описания! User: %d", {message.from_user.id})

    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


@admin_router.callback_query(AddProduct.category)
async def category_choice(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик выбора категории товара

    Args:
        callback (types.CallbackQuery): Callback с выбранной категорией
        state (FSMContext): Контекст машины состояний
        session (AsyncSession): Асинхронная сессия для работы с БД
    """

    logger.info(
        "Обработка выбора категории. User: %d, Выбор: %s",
        callback.from_user.id,
        callback.data,
    )
    if int(cast(str, callback.data)) in [
        category.id for category in await orm_get_categories(session)
    ]:
        await callback.answer()
        await state.update_data(category=callback.data)
        logger.debug("User %d: переход к состоянию ввода цены", callback.from_user.id)
        await callback.message.answer("Теперь введите цену товара.")
        await state.set_state(AddProduct.price)
    else:
        logger.warning("Невалидный выбор категории: %s", callback.data)
        await callback.message.answer("Выберите катеорию из кнопок.")
        await callback.answer()


@admin_router.message(AddProduct.category)
async def category_choice2(message: types.Message):
    """
    Обработчик некорректного выбора категории (текстовый ввод вместо кнопки)

    Args:
        message (types.Message): Сообщение с некорректным вводом
    """
    logger.warning("Некорректный выбор категории! User ID: %d", message.from_user.id)
    await message.answer("'Выберите катеорию из кнопок.'")


@admin_router.message(AddProduct.price, F.text)
async def add_price(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик состояния ввода цены товара

    Args:
        message (types.Message): Сообщение с ценой товара
        state (FSMContext): Контекст машины состояний
    """

    logger.info(
        "Начало обработки цены. Режим: %s",
        "изменение" if AddProduct.product_for_change else "добавление",
    )
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(price=AddProduct.product_for_change.price)
        logger.info("Использована старая цена товара")
    else:
        try:
            float(cast(str, message.text))
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)
        logger.info("Сохранена новая цена товара: %s", message.text)
    logger.debug("Переход к состоянию загрузки изображения")
    await message.answer("Загрузите изображение товара")
    await state.set_state(AddProduct.image)


@admin_router.message(AddProduct.price)
async def add_price2(message: types.Message) -> None:
    """
    Обработчик невалидного ввода цены товара

    Args:
        message (types.Message): Сообщение с невалидными данными
    """
    logger.warning("Невалидный ввод цены! Пользователь: %d", message.from_user.id)

    await message.answer("Вы ввели не допустимые данные, введите стоимость товара")


@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    """
    Обработчик загрузки изображения товара

    Args:
        message (types.Message): Сообщение с изображением или точкой
        state (FSMContext): Контекст машины состояний
        session (AsyncSession): Асинхронная сессия для работы с БД
    """
    logger.info(
        "Начало обработки изображения товара. Режим: %s",
        "изменение" if AddProduct.product_for_change else "добавление",
    )
    if message.text and message.text == "." and AddProduct.product_for_change:
        logger.info("Использовано старое изображение товара")
        await state.update_data(image=AddProduct.product_for_change.image)

    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
        logger.info("Сохранено новое изображение")
    else:
        logger.warning("Неверный формат ввода изображения")
        await message.answer("Отправьте фото продукта")
        return
    data = await state.get_data()
    logger.debug("Данные для сохранения: %s", data)
    if AddProduct.product_for_change:
        logger.info("Обновление товара ID: %d", AddProduct.product_for_change.id)
        await orm_update_product(session, AddProduct.product_for_change.id, data)
    else:
        logger.info("Добавление нового товара")
        await orm_add_product(session, data)
    await message.answer("Товар добавлен/изменен", reply_markup=get_admin_keyboard())
    logger.info("Операция с товаром успешно завершена")
    await state.clear()

    AddProduct.product_for_change = None


@admin_router.message(AddProduct.image)
async def add_image2(message: types.Message) -> None:
    """
    Обработчик невалидного ввода изображения товара
    """
    logger.warning("Невалидный ввод изображения! User ID: %d", message.from_user.id)
    await message.answer("Отправьте фото пищи")
