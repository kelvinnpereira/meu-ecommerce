from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponDiscountType, UserCouponUsage
from app.models.product import Product

USER_ID = "security-user"
HEADERS = {"X-User-ID": USER_ID}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def product(db_session: Session) -> Product:
    p = Product(
        id=10, name="Security Product", price=100.0, stock=50, description="Test"
    )
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture
def test_coupon(db_session: Session) -> Coupon:
    c = Coupon(
        code="SEC10",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=1),
        max_uses_per_user=1,
    )
    db_session.add(c)
    db_session.commit()
    return c


def test_security_headers_present(client: TestClient):
    """SEC-06: Verifies security headers are added to API responses."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers.get("Permissions-Policy", "")


def test_user_id_validation_invalid_characters(client: TestClient):
    """SEC-01: Verifies malformed X-User-ID is rejected."""
    # Test with characters outside allowed alphanumeric, dash, underscore
    response = client.get("/api/v1/cart", headers={"X-User-ID": "bad user!@#$"})
    assert response.status_code == 400
    assert "Invalid X-User-ID header" in response.json()["detail"]


def test_user_id_validation_excessive_length(client: TestClient):
    """SEC-01 & SEC-05: Verifies excessively long X-User-ID is rejected."""
    long_user_id = "a" * 65
    response = client.get("/api/v1/cart", headers={"X-User-ID": long_user_id})
    assert response.status_code == 400
    assert "Invalid X-User-ID header" in response.json()["detail"]


def test_user_id_whitespace_only(client: TestClient):
    """SEC-01: Verifies whitespace-only X-User-ID is treated as missing."""
    response = client.get("/api/v1/cart", headers={"X-User-ID": "   "})
    assert response.status_code == 400
    assert "X-User-ID header missing" in response.json()["detail"]


def test_add_item_quantity_upper_bound(client: TestClient, product: Product):
    """SEC-05: Verifies quantity over max limit (9999) is rejected with 422."""
    response = client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 10000},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_add_item_non_numeric_product_id(client: TestClient):
    """SEC-05: Verifies non-numeric product_id is rejected by schema with 422."""
    response = client.post(
        "/api/v1/cart/items",
        json={"product_id": "malicious_string_not_id", "quantity": 1},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_coupon_code_length_limit(client: TestClient, product: Product):
    """SEC-05: Verifies oversized coupon codes are rejected with 422."""
    client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=HEADERS,
    )
    response = client.post(
        "/api/v1/cart/coupon",
        json={"coupon_code": "A" * 51},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_coupon_expiration_revalidated_at_confirm_order(
    client: TestClient, product: Product, db_session: Session
):
    """
    SEC-02: Verifies that if a coupon was valid when added to the cart,
    but expired prior to order confirmation, the order confirmation fails with 422.
    """
    # Create coupon expiring very soon
    expiring_coupon = Coupon(
        code="EXPIRE_SOON",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=15.0,
        expires_at=utc_now() + timedelta(seconds=10),
        max_uses_per_user=1,
    )
    db_session.add(expiring_coupon)
    db_session.commit()

    # Add item
    client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=HEADERS,
    )

    # Apply coupon while valid
    apply_res = client.post(
        "/api/v1/cart/coupon",
        json={"coupon_code": "EXPIRE_SOON"},
        headers=HEADERS,
    )
    assert apply_res.status_code == 200

    # Start checkout
    checkout_res = client.post("/api/v1/cart/checkout", headers=HEADERS)
    assert checkout_res.status_code == 200

    # Simulate coupon expiration before confirming order
    expiring_coupon.expires_at = utc_now() - timedelta(minutes=10)
    db_session.commit()

    # Try to confirm order
    confirm_res = client.post("/api/v1/cart/confirm", headers=HEADERS)
    assert confirm_res.status_code == 422
    assert "Coupon has expired." in confirm_res.json()["detail"]


def test_user_coupon_usage_unique_constraint(db_session: Session, test_coupon: Coupon):
    """
    SEC-03: Verifies database-level UniqueConstraint prevents multiple usages
    of the same coupon by the same user.
    """
    usage1 = UserCouponUsage(
        user_id="user-race", coupon_id=test_coupon.id, order_id="ord-1"
    )
    db_session.add(usage1)
    db_session.commit()

    usage2 = UserCouponUsage(
        user_id="user-race", coupon_id=test_coupon.id, order_id="ord-2"
    )
    db_session.add(usage2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
