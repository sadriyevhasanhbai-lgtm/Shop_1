from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]


def _parse_int_text(value: object) -> int:
    """Matnni butun songa aylantiradi.

    ``1_000`` kabi ajratgichli yozuvlar ataylab rad etiladi.
    """
    if isinstance(value, bool):
        raise ValueError("bool butun son emas")
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise ValueError("butun son matni kutilgan edi")
    text = value.strip()
    if "_" in text:
        raise ValueError("ajratgichli sonlar qabul qilinmaydi")
    try:
        return int(text)
    except ValueError as error:
        raise ValueError("butun son emas") from error


IntFromText = Annotated[int, BeforeValidator(_parse_int_text)]
PositiveIntFromText = Annotated[IntFromText, Field(gt=0)]
NonNegativeIntFromText = Annotated[IntFromText, Field(ge=0)]
MenuChoice = Annotated[IntFromText, Field(ge=0, le=7)]


class _StrippedModel(BaseModel):
    """Matn maydonlarining chetidagi bo'shliqlarni olib tashlaydi."""

    model_config = ConfigDict(str_strip_whitespace=True)


class Product(_StrippedModel):
    """Ombordagi bitta mahsulot."""

    id: NonEmptyStr
    name: NonEmptyStr
    price: PositiveInt
    stock: NonNegativeInt


class ProductList(RootModel[list[Product]]):
    """products.json faylining ildiz modeli."""


class Sale(_StrippedModel):
    """Tarixga yozilgan bitta sotuv."""

    product_id: NonEmptyStr
    name: NonEmptyStr
    quantity: PositiveInt
    unit_price: PositiveInt
    total: NonNegativeInt
    time: str

    @model_validator(mode="after")
    def check_total(self) -> Self:
        """total unit_price * quantity ga teng bo'lishini tekshiradi."""
        if self.total != self.unit_price * self.quantity:
            raise ValueError(
                "total unit_price * quantity ga teng bo'lishi kerak"
            )
        return self


class SaleList(RootModel[list[Sale]]):
    """sales.json faylining ildiz modeli."""


class BestSeller(BaseModel):
    """Hisobot uchun eng ko'p sotilgan mahsulot."""

    name: NonEmptyStr
    quantity: PositiveInt


class NewProductInput(_StrippedModel):
    """Yangi mahsulot qo'shishda kiritilgan matn."""

    product_id: NonEmptyStr
    name: NonEmptyStr
    price: PositiveIntFromText
    stock: NonNegativeIntFromText


class QuantityInput(_StrippedModel):
    """Zaxira yoki sotuv uchun kiritilgan miqdor matni."""

    quantity: PositiveIntFromText


class MenuChoiceInput(_StrippedModel):
    """Menyudan tanlangan bo'lim raqami (0 dan 7 gacha)."""

    choice: MenuChoice


class SearchInput(_StrippedModel):
    """Qidiruv uchun kiritilgan matn."""

    query: str = ""


class RestockInput(QuantityInput):
    """Zaxirani to'ldirish uchun kiritilgan ID va miqdor."""

    product_id: NonEmptyStr


class SaleInput(QuantityInput):
    """Sotuv uchun kiritilgan ID va miqdor."""

    product_id: NonEmptyStr


class ShopReport(BaseModel):
    """Hisobotlar menyusi uchun yig'ilgan statistika."""

    total_revenue: NonNegativeInt
    average_sale: float | None
    best_seller: BestSeller | None
    inventory_value: NonNegativeInt
    low_stock: list[Product]
