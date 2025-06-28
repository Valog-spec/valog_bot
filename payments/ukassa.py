import os

from yookassa import Configuration, Payment

Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")


async def create_payment(amount: float, description: str) -> Payment:
    """
    Создает платеж через YooMoney API.

    Args:
        amount (float): Сумма платежа в рублях
        description (str): Описание платежа (видимое пользователю)

    Returns:
        Payment: Объект платежа YooMoney

    """
    payment = Payment.create(
        {
            "amount": {"value": str(amount), "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/Valog_aiogram3_bot",
            },
            "capture": True,
            "description": description,
            "test": True,
        }
    )
    return payment
