from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.cart import CartStatusEnum
from app.models.coupon import Coupon, CouponDiscountType
from app.models.product import Product
from app.services.cart_service import CartEmptyError, CartService
from app.services.coupon_service import (
    CouponExpiredError,
    CouponInvalidError,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def cart_service(db_session: Session) -> CartService:
    return CartService(db_session)


@pytest.fixture
def sample_product(db_session: Session) -> Product:
    product = Product(
        name="Notebook Gamer",
        description="Core i7 16GB",
        price=5000.00,
        stock=10,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_apply_valid_percentage_coupon(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_percentage"
    coupon = Coupon(
        code="PROMO10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=30),
    )
    db_session.add(coupon)
    db_session.commit()
    db_session.refresh(coupon)

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)

    cart = cart_service.apply_coupon(user_id, "PROMO10")

    assert cart.coupon_id == coupon.id
    assert cart.coupon.code == "PROMO10"


def test_apply_valid_fixed_coupon(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_fixed"
    coupon = Coupon(
        code="FIXO50",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=50.0,
        expires_at=utc_now() + timedelta(days=30),
    )
    db_session.add(coupon)
    db_session.commit()
    db_session.refresh(coupon)

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)

    cart = cart_service.apply_coupon(user_id, "FIXO50")

    assert cart.coupon_id == coupon.id
    assert cart.coupon.code == "FIXO50"


def test_apply_invalid_coupon(cart_service: CartService, sample_product: Product):
    user_id = "user_test_invalid"
    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)

    with pytest.raises(CouponInvalidError):
        cart_service.apply_coupon(user_id, "NONEXISTENT")


def test_apply_expired_coupon(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_expired"
    coupon = Coupon(
        code="EXPIRED20",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=20.0,
        expires_at=utc_now() - timedelta(days=5),
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)

    with pytest.raises(CouponExpiredError):
        cart_service.apply_coupon(user_id, "EXPIRED20")


def test_remove_coupon(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_remove"
    coupon = Coupon(
        code="CUPOM_REM",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=15.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)
    cart = cart_service.apply_coupon(user_id, "CUPOM_REM")
    assert cart.coupon_id is not None

    cart_after_remove = cart_service.remove_coupon(user_id)
    assert cart_after_remove.coupon_id is None


def test_replace_coupon(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_replace"
    c1 = Coupon(
        code="C1",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    c2 = Coupon(
        code="C2",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=30.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add_all([c1, c2])
    db_session.commit()
    db_session.refresh(c2)

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)
    cart_service.apply_coupon(user_id, "C1")
    cart_updated = cart_service.apply_coupon(user_id, "C2")

    assert cart_updated.coupon_id == c2.id
    assert cart_updated.coupon.code == "C2"


def test_apply_coupon_to_empty_cart(cart_service: CartService, db_session: Session):
    user_id = "user_test_empty"
    coupon = Coupon(
        code="EMPTY10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.get_or_create_cart(user_id)

    with pytest.raises(CartEmptyError):
        cart_service.apply_coupon(user_id, "EMPTY10")


def test_coupon_removed_when_cart_emptied(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    user_id = "user_test_empty_cart_removes_coupon"
    coupon = Coupon(
        code="DISC10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=1)
    cart = cart_service.apply_coupon(user_id, "DISC10")
    assert cart.coupon_id is not None

    cart_empty = cart_service.remove_item(user_id, product_id=str(sample_product.id))
    assert cart_empty.coupon_id is None
    assert cart_empty.status == CartStatusEnum.EMPTY
