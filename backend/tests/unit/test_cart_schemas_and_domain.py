from decimal import Decimal

from app.models.coupon import CouponDiscountType
from app.schemas.cart import CartItemRead, CartRead, CouponRead


def test_cart_item_subtotal_calculation():
    """Unit test: CartItemRead calculates subtotal as unit_price * quantity."""
    item = CartItemRead(
        id=1,
        product_id="101",
        quantity=3,
        unit_price=Decimal("49.90"),
    )
    assert item.subtotal == Decimal("149.70")


def test_cart_read_empty_cart_totals():
    """Unit test: Empty cart has zero subtotal, zero discount and zero total."""
    cart = CartRead(
        id=1,
        user_id="usr_empty",
        status="EMPTY",
        items=[],
        coupon=None,
    )
    assert cart.subtotal == Decimal("0.00")
    assert cart.discount == Decimal("0.00")
    assert cart.total == Decimal("0.00")


def test_cart_read_subtotal_with_multiple_items():
    """Unit test: Subtotal is the exact sum of all item subtotals."""
    items = [
        CartItemRead(id=1, product_id="1", quantity=2, unit_price=Decimal("150.00")),
        CartItemRead(id=2, product_id="2", quantity=1, unit_price=Decimal("350.00")),
    ]
    cart = CartRead(
        id=1,
        user_id="usr_123",
        status="WITH_ITEMS",
        items=items,
        coupon=None,
    )
    assert cart.subtotal == Decimal("650.00")
    assert cart.discount == Decimal("0.00")
    assert cart.total == Decimal("650.00")


def test_cart_read_percentage_coupon_discount():
    """RN-004: Percentage discount calculates total_itens * (valor_cupom / 100)."""
    items = [
        CartItemRead(id=1, product_id="1", quantity=1, unit_price=Decimal("1000.00")),
    ]
    coupon = CouponRead(
        id=1,
        code="PROMO15",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=Decimal("15.00"),
    )
    cart = CartRead(
        id=1,
        user_id="usr_123",
        status="WITH_ITEMS",
        items=items,
        coupon=coupon,
    )
    assert cart.subtotal == Decimal("1000.00")
    assert cart.discount == Decimal("150.00")
    assert cart.total == Decimal("850.00")


def test_cart_read_fixed_coupon_discount_normal():
    """RN-004: Fixed discount calculates min(valor_cupom, total_itens)."""
    items = [
        CartItemRead(id=1, product_id="1", quantity=2, unit_price=Decimal("100.00")),
    ]
    coupon = CouponRead(
        id=2,
        code="FIXO50",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=Decimal("50.00"),
    )
    cart = CartRead(
        id=1,
        user_id="usr_123",
        status="WITH_ITEMS",
        items=items,
        coupon=coupon,
    )
    assert cart.subtotal == Decimal("200.00")
    assert cart.discount == Decimal("50.00")
    assert cart.total == Decimal("150.00")


def test_cart_read_fixed_coupon_discount_floor_zero():
    """RN-004: When fixed coupon exceeds subtotal, total cannot be negative (floor zero)."""
    items = [
        CartItemRead(id=1, product_id="1", quantity=1, unit_price=Decimal("75.00")),
    ]
    coupon = CouponRead(
        id=3,
        code="MEGABONUS200",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=Decimal("200.00"),
    )
    cart = CartRead(
        id=1,
        user_id="usr_123",
        status="WITH_ITEMS",
        items=items,
        coupon=coupon,
    )
    assert cart.subtotal == Decimal("75.00")
    assert cart.discount == Decimal("75.00")
    assert cart.total == Decimal("0.00")
