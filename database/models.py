from typing import Annotated

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class Base(DeclarativeBase):
    """
    Базовый класс моделей SQLAlchemy

    Attributes:
        created (DateTime): Дата создания записи (автоматически устанавливается при создании)
        updated (DateTime): Дата последнего обновления записи (автоматически обновляется)
    """

    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class Banner(Base):
    """
    Модель баннера для страниц c информацией

    Attributes:
        id (int): Уникальный идентификатор баннера
        name (str): Название баннера (уникальное, макс. 15 символов)
        image (str | None): Ссылка на изображение
        description (str | None): Текстовое описание баннера
    """

    __tablename__ = "banner"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Category(Base):
    """
    Модель категории товаров.

    Attributes:
        id (int): Уникальный идентификатор категории
        name (str): Название категории
    """

    __tablename__ = "category"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class Product(Base):
    """
    Модель товара в магазине.

    Attributes:
        id (int): Уникальный идентификатор товара
        name (str): Название товара
        description (str): Подробное описание товара
        price (float): Цена товара
        image (str): Ссылка на изображение товара
        category_id (int): Ссылка на категорию (внешний ключ)
        category (Category): Связь с категорией
    """

    __tablename__ = "product"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped["Category"] = relationship(backref="product")


class User(Base):
    """
    Модель пользователя системы.

    Attributes:
        id (int): Уникальный идентификатор пользователя
        user_id (int): Идентификатор пользователя в Telegram
        first_name (str | None): Имя пользователя
        last_name (str | None): Фамилия пользователя
        cart (Cart): Связь с корзиной пользователя.
    """

    __tablename__ = "user"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)

    cart: Mapped["Cart"] = relationship(back_populates="user")


class Cart(Base):
    """
    Модель корзины пользователя.

    Attributes:
        id (int): Уникальный идентификатор в корзине.
        user_id (int): Ссылка на пользователя (внешний ключ)
        product_id (int): Ссылка на товар (внешний ключ)
        quantity (int): Количество товара
        user (User): Связь с пользователем.
        product (Product): Связь с товаром
    """

    __tablename__ = "cart"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int]

    user: Mapped["User"] = relationship(back_populates="cart")
    product: Mapped["Product"] = relationship(backref="cart")


class Order(Base):
    """
    Модель заказа.

    Attributes:
        id (int): Уникальный идентификатор заказа
        full_name (str): Полное имя получателя
        user_id (int): Ссылка на пользователя (внешний ключ)
        phone (str | None): Контактный телефон
        product_id (int): Ссылка на товар (внешний ключ)
        paid (bool): Статус оплаты
        total_price (float): Общая сумма заказа
        status (str): Текущий статус заказа
        address (str): Адрес доставки
        user (User): Связьс пользователем
        product (Product): Связь с товаром
    """

    __tablename__ = "order"

    id: Mapped[intpk]
    full_name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"))
    phone: Mapped[str] = mapped_column(String(13), nullable=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    paid: Mapped[bool] = mapped_column(default=False)
    total_price: [float] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str]
    address: Mapped[str]

    user: Mapped["User"] = relationship(backref="order")
    product: Mapped["Product"] = relationship(backref="product")
