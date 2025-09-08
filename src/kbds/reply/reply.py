from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_keyboard(
    *btns: str,
    placeholder: str | None = None,
    request_contact: int | None = None,
    request_location: int | None = None,
    sizes: tuple[int] = (2,),
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Создает кастомную клавиатуру с различными типами кнопок

    Args:
        *btns (str): Произвольное количество текстов для кнопок
        placeholder (str): Подсказка в поле ввода
        request_contact (int): Индекс кнопки для запроса контакта
        request_location (int): Индекс кнопки для запроса геолокации
        sizes (tuple[int]): Распределение кнопок по рядам

    Returns:
        ReplyKeyboardMarkup: Объект клавиатуры с настроенными кнопками
    """

    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):

        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))

        elif request_location and request_location == index:
            keyboard.add(
                KeyboardButton(
                    text=text,
                    request_location=True,
                )
            )
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder
    )


def contact() -> ReplyKeyboardMarkup:
    """
    Создает стандартную клавиатуру с одной кнопкой для отправки номера телефона

    Returns:
      ReplyKeyboardMarkup: Клавиатура с кнопкой отправить номер телефона
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
