from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.cart import CartStatusEnum
from app.models.coupon import Coupon, CouponDiscountType
from app.models.product import Product
from app.services.cart_service import (
    CartEmptyError,
    CartService,
    InsufficientStockError,
    InvalidTransitionError,
)
from app.services.coupon_service import (
    CouponExpiredError,
    InvalidCouponError,
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


# --- State Machine Tests ---


def test_cart_initial_state(cart_service: CartService):
    user_id = "user_initial_state"
    cart = cart_service.get_or_create_cart(user_id)
    assert cart.status == CartStatusEnum.EMPTY


def test_transition_empty_to_with_items(
    cart_service: CartService, sample_product: Product
):
    user_id = "user_empty_to_with_items"
    cart = cart_service.add_item(user_id, str(sample_product.id), 1)
    assert cart.status == CartStatusEnum.WITH_ITEMS


def test_transition_with_items_to_empty(
    cart_service: CartService, sample_product: Product
):
    user_id = "user_with_items_to_empty"
    cart_service.add_item(user_id, str(sample_product.id), 1)
    cart = cart_service.remove_item(user_id, str(sample_product.id))
    assert cart.status == CartStatusEnum.EMPTY


def test_transition_with_items_to_checkout(
    cart_service: CartService, sample_product: Product
):
    user_id = "user_with_items_to_checkout"
    cart_service.add_item(user_id, str(sample_product.id), 1)
    cart = cart_service.start_checkout(user_id)
    assert cart.status == CartStatusEnum.IN_CHECKOUT


def test_transition_checkout_to_with_items(
    cart_service: CartService, sample_product: Product
):
    user_id = "user_checkout_to_with_items"
    cart_service.add_item(user_id, str(sample_product.id), 1)
    cart_service.start_checkout(user_id)
    cart = cart_service.return_to_cart(user_id)
    assert cart.status == CartStatusEnum.WITH_ITEMS


def test_transition_checkout_to_order_created(
    cart_service: CartService, sample_product: Product
):
    user_id = "user_checkout_to_order_created"
    cart_service.add_item(user_id, str(sample_product.id), 1)
    cart_service.start_checkout(user_id)
    cart = cart_service.confirm_order(user_id)
    assert cart.status == CartStatusEnum.ORDER_CREATED


@pytest.mark.parametrize(
    "initial_state_actions, invalid_action, expected_error",
    [
        (
            [],  # EMPTY
            lambda service, uid: service.start_checkout(uid),
            CartEmptyError,
        ),
        (
            [lambda service, uid, pid: service.add_item(uid, pid, 1)],  # WITH_ITEMS
            lambda service, uid: service.confirm_order(uid),
            InvalidTransitionError,
        ),
        (
            [
                lambda service, uid, pid: service.add_item(uid, pid, 1),
                lambda service, uid, pid: service.start_checkout(uid),
                lambda service, uid, pid: service.confirm_order(uid),
            ],  # ORDER_CREATED
            lambda service, uid: service.start_checkout(uid),
            InvalidTransitionError,
        ),
        (
            [
                lambda service, uid, pid: service.add_item(uid, pid, 1),
                lambda service, uid, pid: service.start_checkout(uid),
                lambda service, uid, pid: service.confirm_order(uid),
            ],  # ORDER_CREATED
            lambda service, uid: service.add_item(uid, "99", 1),
            InvalidTransitionError,
        ),
    ],
)
def test_invalid_transitions(
    cart_service: CartService,
    sample_product: Product,
    initial_state_actions,
    invalid_action,
    expected_error,
):
    user_id = "user_invalid_transition"
    product_id = str(sample_product.id)

    # Setup state
    for action in initial_state_actions:
        action(cart_service, user_id, product_id)

    # Perform invalid action
    with pytest.raises(expected_error):
        invalid_action(cart_service, user_id)


# --- Existing Coupon Tests ---


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

    with pytest.raises(InvalidCouponError):
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


def test_confirm_order_stock_conflict_rolls_back_and_preserves_checkout_state(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    """RN-007: Test atomic rollback when stock becomes insufficient during confirmation."""
    user_id = "user_test_confirm_rollback"
    coupon = Coupon(
        code="ROLLBACK10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.add_item(user_id, product_id=str(sample_product.id), quantity=5)
    cart_service.apply_coupon(user_id, "ROLLBACK10")
    cart_service.start_checkout(user_id)

    # Concurrently reduce product stock below requested quantity
    sample_product.stock = 2
    db_session.commit()

    with pytest.raises(InsufficientStockError):
        cart_service.confirm_order(user_id)

    # Cart must remain in IN_CHECKOUT and product stock must remain 2 (not decremented)
    cart = cart_service.get_or_create_cart(user_id)
    assert cart.status == CartStatusEnum.IN_CHECKOUT
    db_session.refresh(sample_product)
    assert sample_product.stock == 2


def test_return_to_cart_when_not_in_checkout_raises_invalid_transition(
    cart_service: CartService, sample_product: Product
):
    """RF-009: return_to_cart must only be allowed from IN_CHECKOUT state."""
    user_id = "user_test_return_invalid"
    cart_service.get_or_create_cart(user_id)

    # From EMPTY
    with pytest.raises(InvalidTransitionError):
        cart_service.return_to_cart(user_id)

    # From WITH_ITEMS
    cart_service.add_item(user_id, str(sample_product.id), 1)
    with pytest.raises(InvalidTransitionError):
        cart_service.return_to_cart(user_id)


def test_new_cart_created_after_previous_order_completed(
    cart_service: CartService, sample_product: Product
):
    """RN-009: After confirming an order, attempting mutation fails, but user can explicitly start a new active cart."""
    user_id = "user_test_new_cart_post_order"
    cart_service.add_item(user_id, str(sample_product.id), 2)
    cart_service.start_checkout(user_id)
    first_cart = cart_service.confirm_order(user_id)
    assert first_cart.status == CartStatusEnum.ORDER_CREATED

    # Attempting to mutate the confirmed cart fails
    with pytest.raises(InvalidTransitionError):
        cart_service.add_item(user_id, str(sample_product.id), 1)

    # User explicitly starts a new cart (RF-001)
    new_cart = cart_service.create_cart(user_id)
    assert new_cart.id != first_cart.id
    assert new_cart.status == CartStatusEnum.EMPTY
    assert len(new_cart.items) == 0

    # User can add items to the new cart normally
    updated_cart = cart_service.add_item(user_id, str(sample_product.id), 1)
    assert updated_cart.status == CartStatusEnum.WITH_ITEMS
    assert len(updated_cart.items) == 1


def test_integration_cart_abandonment_flow(
    cart_service: CartService, sample_product: Product
):
    """RF-011: Cart can be transitioned to ABANDONED from any active state and is terminal."""
    # 1. Abandon from EMPTY
    user_empty = "usr_abandon_empty"
    cart_empty = cart_service.abandon_cart(user_empty)
    assert cart_empty.status == CartStatusEnum.ABANDONED

    # Terminal check: Cannot mutate abandoned cart
    with pytest.raises(InvalidTransitionError):
        cart_service.add_item(user_empty, str(sample_product.id), 1)

    # 2. Abandon from WITH_ITEMS
    user_items = "usr_abandon_items"
    cart_service.add_item(user_items, str(sample_product.id), 1)
    cart_items = cart_service.abandon_cart(user_items)
    assert cart_items.status == CartStatusEnum.ABANDONED

    # 3. Abandon from IN_CHECKOUT
    user_checkout = "usr_abandon_checkout"
    cart_service.add_item(user_checkout, str(sample_product.id), 1)
    cart_service.start_checkout(user_checkout)
    cart_checkout = cart_service.abandon_cart(user_checkout)
    assert cart_checkout.status == CartStatusEnum.ABANDONED


def test_integration_coupon_replacement(
    cart_service: CartService, db_session: Session, sample_product: Product
):
    """RN-001: Successive coupon applications replace the previous coupon."""
    user_id = "usr_coupon_replace"
    c1 = Coupon(
        code="PRIMEIRO10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    c2 = Coupon(
        code="SEGUNDO20",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=20.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    cart_service.add_item(user_id, str(sample_product.id), 1)
    cart = cart_service.apply_coupon(user_id, "PRIMEIRO10")
    assert cart.coupon_id == c1.id

    # Applying c2 replaces c1
    cart = cart_service.apply_coupon(user_id, "SEGUNDO20")
    assert cart.coupon_id == c2.id


def test_integration_fixed_coupon_exceeding_subtotal_persists_correctly(
    cart_service: CartService, db_session: Session
):
    """RN-004: Fixed coupon exceeding subtotal is persisted and verified."""
    user_id = "usr_fixed_floor_zero"
    cheap_product = Product(
        name="Cabo USB-C", description="Cabo 1m", price=30.00, stock=10
    )
    big_coupon = Coupon(
        code="FIXO50",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=50.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    db_session.add_all([cheap_product, big_coupon])
    db_session.commit()

    cart_service.add_item(user_id, str(cheap_product.id), 1)
    cart = cart_service.apply_coupon(user_id, "FIXO50")

    assert cart.coupon_id == big_coupon.id
    from app.schemas.cart import CartRead

    cart_read = CartRead.model_validate(cart)
    assert cart_read.subtotal == 30.00
    assert cart_read.discount == 30.00
    assert cart_read.total == 0.00


def test_integration_confirm_order_deadlock_prevention_ordering(
    cart_service: CartService, db_session: Session
):
    """RN-006 / RN-007: Confirm order locks and decrements products in ascending product_id order."""
    user_id = "usr_deadlock_test"
    p1 = Product(id=10, name="Item 10", price=100.0, stock=5)
    p2 = Product(id=20, name="Item 20", price=200.0, stock=5)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Add items in reverse order (20 first, then 10)
    cart_service.add_item(user_id, "20", 2)
    cart_service.add_item(user_id, "10", 1)
    cart_service.start_checkout(user_id)

    confirmed_cart = cart_service.confirm_order(user_id)
    assert confirmed_cart.status == CartStatusEnum.ORDER_CREATED

    db_session.refresh(p1)
    db_session.refresh(p2)
    assert p1.stock == 4
    assert p2.stock == 3
