import pytest

from app.models.cart import CartStatusEnum
from app.services.cart_service import (
    CartEmptyError,
    CartItemNotFoundError,
    CartService,
    InsufficientStockError,
    InvalidTransitionError,
    ProductNotFoundError,
)
from tests.fixtures.factories import (
    REALISTIC_COUPONS,
    REALISTIC_PRODUCTS,
    build_coupon,
    build_product,
)
from tests.unit.doubles import (
    FakeCartRepository,
    MockDbSession,
    SpyCouponService,
    StubProductService,
)


@pytest.fixture
def fake_cart_repo():
    return FakeCartRepository()


@pytest.fixture
def mock_db(fake_cart_repo):
    return MockDbSession(cart_repository=fake_cart_repo)


@pytest.fixture
def stub_product_service():
    p1 = build_product(
        id=1,
        name=REALISTIC_PRODUCTS["laptop"]["name"],
        price=REALISTIC_PRODUCTS["laptop"]["price"],
        stock=REALISTIC_PRODUCTS["laptop"]["stock"],
        description=REALISTIC_PRODUCTS["laptop"]["description"],
    )
    p2 = build_product(
        id=2,
        name=REALISTIC_PRODUCTS["mouse"]["name"],
        price=REALISTIC_PRODUCTS["mouse"]["price"],
        stock=REALISTIC_PRODUCTS["mouse"]["stock"],
        description=REALISTIC_PRODUCTS["mouse"]["description"],
    )
    p3 = build_product(
        id=3,
        name=REALISTIC_PRODUCTS["monitor_low_stock"]["name"],
        price=REALISTIC_PRODUCTS["monitor_low_stock"]["price"],
        stock=REALISTIC_PRODUCTS["monitor_low_stock"]["stock"],
        description=REALISTIC_PRODUCTS["monitor_low_stock"]["description"],
    )
    return StubProductService(products=[p1, p2, p3])


@pytest.fixture
def spy_coupon_service():
    c1 = build_coupon(
        id=10,
        code=REALISTIC_COUPONS["percentage_10"]["code"],
        discount_type=REALISTIC_COUPONS["percentage_10"]["discount_type"],
        value=REALISTIC_COUPONS["percentage_10"]["value"],
    )
    c2 = build_coupon(
        id=20,
        code=REALISTIC_COUPONS["fixed_50"]["code"],
        discount_type=REALISTIC_COUPONS["fixed_50"]["discount_type"],
        value=REALISTIC_COUPONS["fixed_50"]["value"],
    )
    return SpyCouponService(valid_coupons=[c1, c2])


@pytest.fixture
def cart_service(mock_db, fake_cart_repo, stub_product_service, spy_coupon_service):
    """Instantiates CartService and injects in-memory Test Doubles."""
    service = CartService(db=mock_db)
    service.cart_repository = fake_cart_repo
    service.product_service = stub_product_service
    service.coupon_service = spy_coupon_service
    return service


def test_unit_get_or_create_cart(cart_service, fake_cart_repo):
    """RF-001: get_or_create_cart returns existing or creates a new empty cart."""
    user_id = "usr_client_01"
    cart = cart_service.get_or_create_cart(user_id)
    assert cart is not None
    assert cart.user_id == user_id
    assert cart.status == CartStatusEnum.EMPTY
    assert cart.items == []

    # Calling again returns the exact same cart
    cart2 = cart_service.get_or_create_cart(user_id)
    assert cart2.id == cart.id


def test_unit_add_first_item_transitions_empty_to_with_items(cart_service, mock_db):
    """RF-002: Adding first item transitions status from EMPTY to WITH_ITEMS."""
    user_id = "usr_client_02"
    cart = cart_service.add_item(user_id=user_id, product_id="1", quantity=1)

    assert cart.status == CartStatusEnum.WITH_ITEMS
    assert len(cart.items) == 1
    assert cart.items[0].product_id == "1"
    assert cart.items[0].quantity == 1
    assert mock_db.commit_count >= 1


def test_unit_add_same_item_increments_quantity(cart_service):
    """RF-002: Adding existing product in cart accumulates quantity."""
    user_id = "usr_client_03"
    cart_service.add_item(user_id=user_id, product_id="2", quantity=2)
    cart = cart_service.add_item(user_id=user_id, product_id="2", quantity=3)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 5


def test_unit_add_item_insufficient_stock_raises_error(cart_service):
    """RN-008: Adding quantity greater than available stock raises InsufficientStockError."""
    user_id = "usr_client_04"
    # Product 3 (monitor) only has stock = 1
    with pytest.raises(InsufficientStockError) as exc_info:
        cart_service.add_item(user_id=user_id, product_id="3", quantity=2)

    assert exc_info.value.product_id == "3"
    assert exc_info.value.requested == 2
    assert exc_info.value.available == 1


def test_unit_add_item_invalid_positive_quantity_raises_value_error(cart_service):
    """RN-008: Adding item with quantity <= 0 raises ValueError."""
    user_id = "usr_client_05"
    with pytest.raises(ValueError, match="Quantity must be a positive integer."):
        cart_service.add_item(user_id=user_id, product_id="1", quantity=0)

    with pytest.raises(ValueError, match="Quantity must be a positive integer."):
        cart_service.add_item(user_id=user_id, product_id="1", quantity=-5)


def test_unit_add_item_nonexistent_product_raises_not_found(cart_service):
    """Edge Case: Adding non-existent product raises ProductNotFoundError."""
    user_id = "usr_client_06"
    with pytest.raises(ProductNotFoundError):
        cart_service.add_item(user_id=user_id, product_id="9999", quantity=1)


def test_unit_add_item_to_order_created_raises_invalid_transition(
    cart_service, fake_cart_repo
):
    """RN-009: Attempting to add item to ORDER_CREATED cart raises InvalidTransitionError."""
    user_id = "usr_client_07"
    cart = fake_cart_repo.create(user_id)
    cart.status = CartStatusEnum.ORDER_CREATED

    with pytest.raises(InvalidTransitionError):
        cart_service.add_item(user_id=user_id, product_id="1", quantity=1)


def test_unit_update_item_quantity_success(cart_service):
    """RF-003: Updating item quantity to a valid amount updates the item."""
    user_id = "usr_client_08"
    cart_service.add_item(user_id=user_id, product_id="2", quantity=2)
    cart = cart_service.update_item(user_id=user_id, product_id="2", quantity=7)

    assert cart.items[0].quantity == 7


def test_unit_update_item_quantity_zero_removes_item(cart_service, mock_db):
    """RF-003: Updating item quantity to 0 removes the item from the cart."""
    user_id = "usr_client_09"
    cart_service.add_item(user_id=user_id, product_id="2", quantity=2)
    cart = cart_service.update_item(user_id=user_id, product_id="2", quantity=0)

    assert len(cart.items) == 0
    assert cart.status == CartStatusEnum.EMPTY
    assert len(mock_db.deleted_items) == 1


def test_unit_update_item_insufficient_stock_raises_error(cart_service):
    """RN-008: Updating item to quantity greater than stock raises InsufficientStockError."""
    user_id = "usr_client_10"
    cart_service.add_item(user_id=user_id, product_id="3", quantity=1)

    with pytest.raises(InsufficientStockError):
        cart_service.update_item(user_id=user_id, product_id="3", quantity=5)


def test_unit_update_nonexistent_item_raises_not_found(cart_service):
    """Edge Case: Updating item not present in cart raises CartItemNotFoundError."""
    user_id = "usr_client_11"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)

    with pytest.raises(CartItemNotFoundError):
        cart_service.update_item(user_id=user_id, product_id="2", quantity=2)


def test_unit_remove_last_item_transitions_to_empty_and_clears_coupon(
    cart_service, spy_coupon_service
):
    """RF-004: Removing last item transitions cart to EMPTY and removes coupon."""
    user_id = "usr_client_12"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")
    assert cart_service.get_or_create_cart(user_id).coupon_id == 10

    cart = cart_service.remove_item(user_id=user_id, product_id="1")
    assert cart.status == CartStatusEnum.EMPTY
    assert cart.coupon_id is None
    assert len(cart.items) == 0


def test_unit_apply_coupon_success(cart_service, spy_coupon_service):
    """RF-006: Applying a valid coupon links the coupon to the cart."""
    user_id = "usr_client_13"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart = cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")

    assert cart.coupon_id == 10
    assert len(spy_coupon_service.validated_calls) == 1
    assert spy_coupon_service.validated_calls[0]["code"] == "DESC10"


def test_unit_apply_coupon_to_empty_cart_raises_error(cart_service):
    """Edge Case: Applying coupon to empty cart raises CartEmptyError."""
    user_id = "usr_client_14"
    with pytest.raises(CartEmptyError):
        cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")


def test_unit_remove_coupon_success(cart_service):
    """RF-007: Removing coupon unlinks coupon from the cart."""
    user_id = "usr_client_15"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")

    cart = cart_service.remove_coupon(user_id=user_id)
    assert cart.coupon_id is None


def test_unit_checkout_transitions_with_items_to_in_checkout(cart_service):
    """RF-008: start_checkout transitions cart from WITH_ITEMS to IN_CHECKOUT."""
    user_id = "usr_client_16"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart = cart_service.start_checkout(user_id=user_id)

    assert cart.status == CartStatusEnum.IN_CHECKOUT


def test_unit_checkout_empty_cart_raises_cart_empty_error(cart_service):
    """RF-008: Starting checkout with empty cart raises CartEmptyError."""
    user_id = "usr_client_17"
    with pytest.raises(CartEmptyError):
        cart_service.start_checkout(user_id=user_id)


def test_unit_return_to_cart_from_checkout(cart_service):
    """RF-009: return_to_cart transitions cart from IN_CHECKOUT back to WITH_ITEMS."""
    user_id = "usr_client_18"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart_service.start_checkout(user_id=user_id)

    cart = cart_service.return_to_cart(user_id=user_id)
    assert cart.status == CartStatusEnum.WITH_ITEMS


def test_unit_return_to_cart_when_not_in_checkout_raises_invalid_transition(
    cart_service,
):
    """RF-009 Guard: return_to_cart raises InvalidTransitionError if not IN_CHECKOUT."""
    user_id = "usr_client_19"
    # Cart is EMPTY
    with pytest.raises(InvalidTransitionError):
        cart_service.return_to_cart(user_id=user_id)


def test_unit_abandon_cart_transitions_to_abandoned(cart_service):
    """RF-011: abandon_cart transitions cart to ABANDONED."""
    user_id = "usr_client_20"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=1)
    cart = cart_service.abandon_cart(user_id=user_id)

    assert cart.status == CartStatusEnum.ABANDONED


def test_unit_confirm_order_atomic_success_flow(
    cart_service, stub_product_service, spy_coupon_service, mock_db
):
    """
    RF-010 / RN-006 / RN-007:
    Confirm order verifies stock, decrements stock, marks coupon as used,
    transitions cart to ORDER_CREATED, and commits transaction.
    """
    user_id = "usr_client_21"
    cart_service.add_item(user_id=user_id, product_id="1", quantity=2)
    cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")
    cart_service.start_checkout(user_id=user_id)

    initial_stock = stub_product_service.get_product_by_id(1).stock
    cart = cart_service.confirm_order(user_id=user_id)

    assert cart.status == CartStatusEnum.ORDER_CREATED
    # Stock decremented by 2
    assert stub_product_service.get_product_by_id(1).stock == initial_stock - 2
    # Coupon marked as used
    assert len(spy_coupon_service.used_calls) == 1
    assert spy_coupon_service.used_calls[0]["coupon_id"] == 10
    assert spy_coupon_service.used_calls[0]["user_id"] == user_id
    # Transaction committed
    assert mock_db.commit_count >= 1
    assert mock_db.rollback_count == 0


def test_unit_confirm_order_stock_conflict_rolls_back_transaction(
    cart_service, stub_product_service, spy_coupon_service, mock_db
):
    """
    RN-007: When stock is insufficient during confirmation,
    rollback is executed, coupon is not used, and exception is raised.
    """
    user_id = "usr_client_22"
    cart_service.add_item(user_id=user_id, product_id="3", quantity=1)
    cart_service.apply_coupon(user_id=user_id, coupon_code="DESC10")
    cart_service.start_checkout(user_id=user_id)

    # Concurrently reduce stock of product 3 to 0
    stub_product_service.get_product_by_id(3).stock = 0

    with pytest.raises(InsufficientStockError):
        cart_service.confirm_order(user_id=user_id)

    # Rollback must have been called
    assert mock_db.rollback_count == 1
    # Coupon must NOT have been used
    assert len(spy_coupon_service.used_calls) == 0
    # Cart status remains IN_CHECKOUT
    cart = cart_service.get_or_create_cart(user_id)
    assert cart.status == CartStatusEnum.IN_CHECKOUT
