from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.models.coupon import Coupon, CouponDiscountType
from app.services.coupon_service import (
    CouponAlreadyUsedError,
    CouponExpiredError,
    InvalidCouponError,
    CouponService,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def mock_coupon_repository():
    return MagicMock()


@pytest.fixture
def coupon_service(mock_coupon_repository):
    return CouponService(coupon_repository=mock_coupon_repository)


def test_validate_coupon_success(coupon_service, mock_coupon_repository):
    # Arrange
    valid_coupon = Coupon(
        id=1,
        code="VALIDO",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=10.0,
        expires_at=utc_now() + timedelta(days=1),
    )
    mock_coupon_repository.get_by_code.return_value = valid_coupon
    mock_coupon_repository.get_usage_by_user_and_coupon.return_value = None

    # Act
    result = coupon_service.validate_coupon(code="VALIDO", user_id="user123")

    # Assert
    assert result == valid_coupon
    mock_coupon_repository.get_by_code.assert_called_once_with("VALIDO")
    mock_coupon_repository.get_usage_by_user_and_coupon.assert_called_once_with(
        user_id="user123", coupon_id=1
    )


def test_validate_coupon_not_found(coupon_service, mock_coupon_repository):
    # Arrange
    mock_coupon_repository.get_by_code.return_value = None

    # Act & Assert
    with pytest.raises(InvalidCouponError, match="Coupon does not exist."):
        coupon_service.validate_coupon(code="INEXISTENTE", user_id="user123")

    mock_coupon_repository.get_by_code.assert_called_once_with("INEXISTENTE")


def test_validate_coupon_expired(coupon_service, mock_coupon_repository):
    # Arrange
    expired_coupon = Coupon(
        id=2,
        code="EXPIRADO",
        discount_type=CouponDiscountType.FIXED_VALUE,
        value=50.0,
        expires_at=utc_now() - timedelta(days=1),
    )
    mock_coupon_repository.get_by_code.return_value = expired_coupon

    # Act & Assert
    with pytest.raises(CouponExpiredError, match="Coupon has expired."):
        coupon_service.validate_coupon(code="EXPIRADO", user_id="user123")


def test_validate_coupon_already_used(coupon_service, mock_coupon_repository):
    # Arrange
    used_coupon = Coupon(
        id=3,
        code="USADO",
        discount_type=CouponDiscountType.PERCENTAGE,
        value=15.0,
        expires_at=utc_now() + timedelta(days=10),
    )
    mock_coupon_repository.get_by_code.return_value = used_coupon
    mock_coupon_repository.get_usage_by_user_and_coupon.return_value = MagicMock()

    # Act & Assert
    with pytest.raises(
        CouponAlreadyUsedError, match="Coupon has already been used by this user."
    ):
        coupon_service.validate_coupon(code="USADO", user_id="user123")


def test_validate_coupon_case_insensitive_lookup(
    coupon_service, mock_coupon_repository
):
    # Arrange
    valid_coupon = Coupon(id=1, code="VALIDO", expires_at=utc_now() + timedelta(days=1))
    mock_coupon_repository.get_by_code.return_value = valid_coupon
    mock_coupon_repository.get_usage_by_user_and_coupon.return_value = None

    # Act
    coupon_service.validate_coupon(code="valido", user_id="user123")

    # Assert
    mock_coupon_repository.get_by_code.assert_called_once_with("valido")
