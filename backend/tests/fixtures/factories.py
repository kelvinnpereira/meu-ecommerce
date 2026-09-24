from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from faker import Faker

from app.models.cart import Cart, CartItem, CartStatusEnum
from app.models.coupon import Coupon, CouponDiscountType
from app.models.product import Product

fake = Faker("pt_BR")
fake.seed_instance(42)  # Deterministic seed for reproducible tests


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def build_product(
    id: Optional[int] = None,
    name: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[int] = None,
    description: Optional[str] = None,
) -> Product:
    return Product(
        id=id,
        name=name or fake.catch_phrase(),
        price=(
            price
            if price is not None
            else round(
                float(
                    fake.pydecimal(
                        left_digits=3,
                        right_digits=2,
                        positive=True,
                        min_value=10,
                        max_value=999,
                    )
                ),
                2,
            )
        ),
        stock=stock if stock is not None else fake.random_int(min=5, max=50),
        description=description or fake.sentence(nb_words=10),
    )


def build_coupon(
    id: Optional[int] = None,
    code: Optional[str] = None,
    discount_type: CouponDiscountType = CouponDiscountType.PERCENTAGE,
    value: Optional[float] = None,
    expires_at: Optional[datetime] = None,
    max_uses_per_user: int = 1,
) -> Coupon:
    return Coupon(
        id=id,
        code=code or f"PROMO{fake.random_int(min=10, max=99)}",
        discount_type=discount_type,
        value=(
            value
            if value is not None
            else (10.0 if discount_type == CouponDiscountType.PERCENTAGE else 50.0)
        ),
        expires_at=expires_at or (utc_now() + timedelta(days=30)),
        max_uses_per_user=max_uses_per_user,
    )


def build_cart(
    id: Optional[int] = None,
    user_id: Optional[str] = None,
    status: CartStatusEnum = CartStatusEnum.EMPTY,
    items: Optional[List[CartItem]] = None,
    coupon_id: Optional[int] = None,
) -> Cart:
    cart = Cart(
        id=id or fake.random_int(min=1, max=10000),
        user_id=user_id or f"usr_{fake.uuid4()[:8]}",
        status=status,
        coupon_id=coupon_id,
    )
    cart.items = items if items is not None else []
    return cart


def build_cart_item(
    id: Optional[int] = None,
    cart_id: Optional[int] = None,
    product_id: Optional[str] = None,
    quantity: int = 1,
    unit_price: Optional[Decimal] = None,
) -> CartItem:
    return CartItem(
        id=id or fake.random_int(min=1, max=10000),
        cart_id=cart_id or fake.random_int(min=1, max=10000),
        product_id=product_id or str(fake.random_int(min=1, max=100)),
        quantity=quantity,
        unit_price=unit_price or Decimal("99.90"),
    )


# Catalog of representative realistic products and coupons
REALISTIC_PRODUCTS = {
    "laptop": {
        "name": "Notebook Dell XPS 15",
        "description": "Intel Core i7 13ª Geração, 32GB RAM, SSD 1TB NVMe, Tela OLED 3.5K",
        "price": 8499.90,
        "stock": 5,
    },
    "mouse": {
        "name": "Mouse Sem Fio Logitech MX Master 3S",
        "description": "Sensor Darkfield 8000 DPI, Conexão Bluetooth e Logi Bolt, Silencioso",
        "price": 489.50,
        "stock": 25,
    },
    "teclado": {
        "name": "Teclado Mecânico Keychron K2 Pro",
        "description": "Switches Gateron Brown Hot-Swappable, Wireless Bluetooth, Layout Mac/Win",
        "price": 650.00,
        "stock": 10,
    },
    "monitor_low_stock": {
        "name": "Monitor Ultrawide LG 29WK600",
        "description": "29 polegadas Full HD IPS, 75Hz, HDR10, sRGB 99%",
        "price": 1250.00,
        "stock": 1,  # Edge case: exactly 1 in stock
    },
    "out_of_stock": {
        "name": "Cadeira Ergonômica Herman Miller Aeron",
        "description": "Suporte lombar PostureFit SL, Apoio de braço totalmente ajustável",
        "price": 7200.00,
        "stock": 0,  # Edge case: out of stock
    },
}

REALISTIC_COUPONS = {
    "percentage_10": {
        "code": "DESC10",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": 10.0,
        "expires_in_days": 30,
    },
    "percentage_15": {
        "code": "BLACKFRIDAY15",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": 15.0,
        "expires_in_days": 15,
    },
    "fixed_50": {
        "code": "BEMVINDO50",
        "discount_type": CouponDiscountType.FIXED_VALUE,
        "value": 50.0,
        "expires_in_days": 60,
    },
    "fixed_mega_200": {
        "code": "MEGABONUS200",
        "discount_type": CouponDiscountType.FIXED_VALUE,
        "value": 200.0,
        "expires_in_days": 30,
    },
    "expired": {
        "code": "NATALPASSADO",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": 20.0,
        "expires_in_days": -10,
    },
}
