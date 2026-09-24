from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon, UserCouponUsage
from app.models.product import Product
from app.scripts.seed_volume import seed_volumetric_data


def test_seed_volumetric_data_creates_consistent_dataset(db_session: Session):
    # Act: generate a scaled-down seed run for integration testing
    results = seed_volumetric_data(
        db=db_session,
        clean=True,
        products_target=30,
        coupons_target=15,
        carts_target=25,
    )

    # Assert counts
    assert results["products"] == 30
    assert results["coupons"] == 15
    assert results["carts"] == 25
    assert results["cart_items"] > 0
    assert db_session.query(Product).count() == 30
    assert db_session.query(Coupon).count() == 15
    assert db_session.query(Cart).count() == 25

    # Check that required baseline test fixtures exist
    laptop = db_session.query(Product).filter(Product.name == "Laptop Moderno").first()
    assert laptop is not None
    assert laptop.price == 4500.00

    coupon_10off = db_session.query(Coupon).filter(Coupon.code == "10OFF").first()
    assert coupon_10off is not None
    assert coupon_10off.value == Decimal("10.00")

    # Check relational integrity: all cart items point to valid products
    valid_product_ids = {str(p.id) for p in db_session.query(Product.id).all()}
    for item in db_session.query(CartItem).all():
        assert item.product_id in valid_product_ids
        assert item.quantity > 0
        assert item.unit_price > Decimal("0.00")

    # Check relational integrity: all coupon usages point to valid coupons
    valid_coupon_ids = {c.id for c in db_session.query(Coupon.id).all()}
    for usage in db_session.query(UserCouponUsage).all():
        assert usage.coupon_id in valid_coupon_ids
        assert usage.order_id.startswith("ORD-")


def test_seed_volumetric_data_is_idempotent(db_session: Session):
    # First execution
    first_run = seed_volumetric_data(
        db=db_session,
        clean=True,
        products_target=20,
        coupons_target=10,
        carts_target=15,
    )

    # Second execution without clean flag
    second_run = seed_volumetric_data(
        db=db_session,
        clean=False,
        products_target=20,
        coupons_target=10,
        carts_target=15,
    )

    assert second_run["products"] == first_run["products"]
    assert second_run["coupons"] == first_run["coupons"]
    assert second_run["carts"] == first_run["carts"]
    assert second_run["cart_items"] == first_run["cart_items"]
    assert second_run["user_coupon_usages"] == first_run["user_coupon_usages"]
