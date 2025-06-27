from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories = ['Еда', 'Напитки']

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "about": "Интернет магазин.\nРежим работы - круглосуточно.",
    "payment": as_marked_section(
        Bold("Варианты оплаты:"),
        "ЮKassa",
        marker="✅ ",
    ).as_html(),
    "shipping": as_marked_section(
            Bold("Варианты доставки/заказа:"),
            "Курьер",
            marker="✅ ",
    ).as_html(),
    'catalog': 'Категории:',
    'cart': 'В корзине ничего нет!',
    'orders': "Заказы"
}
