from datetime import datetime, timezone

from app.models.coupon import Coupon
from app.repositories.coupon_repository import CouponRepository


class InvalidCouponError(Exception):
    pass


class CouponExpiredError(InvalidCouponError):
    pass


class CouponAlreadyUsedError(InvalidCouponError):
    pass


class CouponService:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository

    def _validate_coupon_instance(self, coupon: Coupon, user_id: str) -> Coupon:
        now = (
            datetime.now(timezone.utc)
            if coupon.expires_at.tzinfo
            else datetime.now(timezone.utc).replace(tzinfo=None)
        )
        if coupon.expires_at < now:
            raise CouponExpiredError("Coupon has expired.")

        usage = self.coupon_repository.get_usage_by_user_and_coupon(
            user_id=user_id, coupon_id=coupon.id
        )
        if usage:
            raise CouponAlreadyUsedError("Coupon has already been used by this user.")

        return coupon

    def validate_coupon(self, code: str, user_id: str) -> Coupon:
        """
        Validates a coupon by its code for a specific user.

        - Checks if the coupon exists.
        - Checks if the coupon has expired.
        - Checks if the user has already used this coupon.

        Args:
            code: The coupon code.
            user_id: The ID of the user.

        Returns:
            The validated Coupon object.

        Raises:
            InvalidCouponError: If the coupon does not exist.
            CouponExpiredError: If the coupon has expired.
            CouponAlreadyUsedError: If the user has already used the coupon.
        """
        coupon = self.coupon_repository.get_by_code(code)

        if not coupon:
            raise InvalidCouponError("Coupon does not exist.")

        return self._validate_coupon_instance(coupon, user_id)

    def validate_coupon_by_id(self, coupon_id: int, user_id: str) -> Coupon:
        """
        Validates a coupon by its ID for a specific user.
        """
        coupon = self.coupon_repository.get_by_id(coupon_id)

        if not coupon:
            raise InvalidCouponError("Coupon does not exist.")

        return self._validate_coupon_instance(coupon, user_id)

    def mark_coupon_as_used(self, coupon_id: int, user_id: str, order_id: str):
        """
        Marks a coupon as used by a user for a specific order.
        Re-validates that the coupon is valid, not expired, and not already used.
        """
        self.validate_coupon_by_id(coupon_id, user_id)

        self.coupon_repository.create_usage(
            user_id=user_id, coupon_id=coupon_id, order_id=order_id
        )
        # The commit is handled by the calling service that manages the transaction.
