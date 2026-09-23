from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponDiscountType
from app.models.product import Product

USER_ID = "user-123"
HEADERS = {"X-User-ID": USER_ID}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def product_in_stock(db_session: Session) -> Product:
    """Fixture to create a product with sufficient stock."""
    product = Product(
        id=1, name="Test Product 1", price=10.0, stock=10, description="A test product"
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def second_product(db_session: Session) -> Product:
    """Fixture to create another product."""
    product = Product(
        id=2, name="Test Product 2", price=25.0, stock=5, description="Second product"
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def product_out_of_stock(db_session: Session) -> Product:
    """Fixture to create a product with zero stock."""
    product = Product(
        id=3,
        name="Test Product 3",
        price=20.0,
        stock=0,
        description="Out of stock product",
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def valid_percentage_coupon(db_session: Session) -> Coupon:
    coupon = Coupon(
        code="DESC10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=5),
        max_uses_per_user=1,
    )
    db_session.add(coupon)
    db_session.commit()
    return coupon


@pytest.fixture
def valid_fixed_coupon(db_session: Session) -> Coupon:
    coupon = Coupon(
        code="FIXO15",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=15.0,
        expires_at=utc_now() + timedelta(days=5),
        max_uses_per_user=1,
    )
    db_session.add(coupon)
    db_session.commit()
    return coupon


# --- Tests ---


def test_get_cart_for_new_user_creates_empty_cart(client: TestClient):
    """
    T-013: Test getting a cart for a new user should create and return an empty cart.
    Corresponds to RF-001, RF-005.
    """
    response = client.get("/api/v1/cart", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == USER_ID
    assert data["status"] == "EMPTY"
    assert data["items"] == []
    assert Decimal(str(data["total"])) == Decimal("0.00")


def test_add_item_to_cart_success(client: TestClient, product_in_stock: Product):
    """
    T-013: Test successfully adding an item to the cart.
    Corresponds to RF-002.
    """
    item_data = {"product_id": str(product_in_stock.id), "quantity": 2}
    response = client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WITH_ITEMS"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(product_in_stock.id)
    assert data["items"][0]["quantity"] == 2
    assert Decimal(str(data["total"])) == Decimal("20.00")


def test_add_same_item_increments_quantity(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Adding same product increments quantity.
    """
    item_data = {"product_id": str(product_in_stock.id), "quantity": 2}
    client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)

    response = client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 4
    assert Decimal(str(data["total"])) == Decimal("40.00")


def test_add_nonexistent_item_to_cart_fails(client: TestClient):
    """
    T-013: Adding a product that does not exist fails with 422.
    """
    item_data = {"product_id": "999", "quantity": 1}
    response = client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)

    assert response.status_code == 422
    assert "Product with id 999 not found" in response.json()["detail"]


def test_add_item_with_insufficient_stock_fails(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Adding a product with insufficient stock fails with 422.
    Corresponds to RN-008.
    """
    item_data = {"product_id": str(product_in_stock.id), "quantity": 11}
    response = client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)

    assert response.status_code == 422
    assert "Insufficient stock" in response.json()["detail"]


def test_add_item_from_out_of_stock_product_fails(
    client: TestClient, product_out_of_stock: Product
):
    """
    T-013: Adding an out of stock product fails with 422.
    """
    item_data = {"product_id": str(product_out_of_stock.id), "quantity": 1}
    response = client.post("/api/v1/cart/items", headers=HEADERS, json=item_data)

    assert response.status_code == 422
    assert "Insufficient stock" in response.json()["detail"]


def test_add_item_requires_user_id_header(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Test that X-User-ID header is required.
    """
    item_data = {"product_id": str(product_in_stock.id), "quantity": 1}
    response = client.post("/api/v1/cart/items", json=item_data)

    assert response.status_code == 400
    assert "X-User-ID header missing" in response.json()["detail"]


def test_update_item_quantity_success(client: TestClient, product_in_stock: Product):
    """
    T-013: Updating item quantity in cart.
    Corresponds to RF-003.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 2},
    )

    response = client.put(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
        json={"quantity": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["quantity"] == 5
    assert Decimal(str(data["total"])) == Decimal("50.00")


def test_update_item_quantity_zero_removes_item(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Updating item quantity to 0 removes the item and empties the cart.
    Corresponds to RF-003, RF-004.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 2},
    )

    response = client.put(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
        json={"quantity": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "EMPTY"
    assert len(data["items"]) == 0
    assert Decimal(str(data["total"])) == Decimal("0.00")


def test_update_item_insufficient_stock_fails(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Updating to a quantity exceeding stock fails with 422.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 2},
    )

    response = client.put(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
        json={"quantity": 20},
    )
    assert response.status_code == 422
    assert "Insufficient stock" in response.json()["detail"]


def test_update_nonexistent_item_fails(client: TestClient):
    """
    T-013: Updating an item not in cart fails with 404.
    """
    response = client.put(
        "/api/v1/cart/items/999",
        headers=HEADERS,
        json={"quantity": 1},
    )
    assert response.status_code == 404


def test_remove_item_success(
    client: TestClient, product_in_stock: Product, second_product: Product
):
    """
    T-013: Removing an item from cart with multiple items leaves remaining item.
    Corresponds to RF-004.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 1},
    )
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(second_product.id), "quantity": 1},
    )

    response = client.delete(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WITH_ITEMS"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(second_product.id)
    assert Decimal(str(data["total"])) == Decimal("25.00")


def test_remove_nonexistent_item_fails(client: TestClient):
    """
    T-013: Removing an item not in cart fails with 404.
    """
    response = client.delete("/api/v1/cart/items/999", headers=HEADERS)
    assert response.status_code == 404


def test_apply_and_remove_coupon_flow(
    client: TestClient, product_in_stock: Product, valid_percentage_coupon: Coupon
):
    """
    T-013: Apply coupon and remove coupon from cart.
    Corresponds to RF-006, RF-007, RN-001, RN-004.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 2},
    )  # subtotal = 20.00

    # Apply coupon
    response = client.post(
        "/api/v1/cart/coupon",
        headers=HEADERS,
        json={"coupon_code": valid_percentage_coupon.code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["coupon"]["code"] == valid_percentage_coupon.code
    assert Decimal(str(data["discount"])) == Decimal("2.00")  # 10% of 20.00
    assert Decimal(str(data["total"])) == Decimal("18.00")

    # Remove coupon
    response = client.delete("/api/v1/cart/coupon", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["coupon"] is None
    assert Decimal(str(data["discount"])) == Decimal("0.00")
    assert Decimal(str(data["total"])) == Decimal("20.00")


def test_apply_coupon_to_empty_cart_fails(
    client: TestClient, valid_percentage_coupon: Coupon
):
    """
    T-013: Applying coupon to empty cart fails with 422.
    """
    response = client.post(
        "/api/v1/cart/coupon",
        headers=HEADERS,
        json={"coupon_code": valid_percentage_coupon.code},
    )
    assert response.status_code == 422


def test_apply_invalid_coupon_fails(client: TestClient, product_in_stock: Product):
    """
    T-013: Applying invalid coupon fails with 422.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 1},
    )

    response = client.post(
        "/api/v1/cart/coupon",
        headers=HEADERS,
        json={"coupon_code": "INVALIDO"},
    )
    assert response.status_code == 422


def test_checkout_and_return_to_cart_flow(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Start checkout and return to cart.
    Corresponds to RF-008, RF-009.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 1},
    )

    # Start checkout
    response = client.post("/api/v1/cart/checkout", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "IN_CHECKOUT"

    # Modifying in checkout should fail with 409
    resp_modify = client.put(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
        json={"quantity": 2},
    )
    assert resp_modify.status_code == 409

    # Return to cart
    response = client.delete("/api/v1/cart/checkout", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "WITH_ITEMS"

    # Now modifying works again
    resp_modify_after = client.put(
        f"/api/v1/cart/items/{product_in_stock.id}",
        headers=HEADERS,
        json={"quantity": 2},
    )
    assert resp_modify_after.status_code == 200
    assert resp_modify_after.json()["items"][0]["quantity"] == 2


def test_checkout_empty_cart_fails(client: TestClient):
    """
    T-013: Starting checkout on empty cart fails with 422.
    """
    response = client.post("/api/v1/cart/checkout", headers=HEADERS)
    assert response.status_code == 422


def test_confirm_order_flow(
    client: TestClient,
    product_in_stock: Product,
    valid_percentage_coupon: Coupon,
    db_session: Session,
):
    """
    T-013: Confirm order in checkout transitions to ORDER_CREATED and decrements stock.
    Corresponds to RF-010, RN-006, RN-009.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 3},
    )
    client.post(
        "/api/v1/cart/coupon",
        headers=HEADERS,
        json={"coupon_code": valid_percentage_coupon.code},
    )
    client.post("/api/v1/cart/checkout", headers=HEADERS)

    # Confirm order
    response = client.post("/api/v1/cart/confirm", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["cart_status"] == "ORDER_CREATED"

    # Check stock was decremented in database
    db_session.refresh(product_in_stock)
    assert product_in_stock.stock == 7  # 10 - 3

    # Any subsequent modification on cart should fail with 409
    resp_after = client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 1},
    )
    assert resp_after.status_code == 409


def test_confirm_order_not_in_checkout_fails(
    client: TestClient, product_in_stock: Product
):
    """
    T-013: Confirming order without being in checkout fails with 409.
    """
    client.post(
        "/api/v1/cart/items",
        headers=HEADERS,
        json={"product_id": str(product_in_stock.id), "quantity": 1},
    )
    # Cart is WITH_ITEMS, not IN_CHECKOUT
    response = client.post("/api/v1/cart/confirm", headers=HEADERS)
    assert response.status_code == 409
