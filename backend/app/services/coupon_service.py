from datetime import datetime, timezone

from app.models.coupon import Coupon
from app.repositories.coupon_repository import CouponRepository


class CouponInvalidError(Exception):
    pass


class CouponExpiredError(Exception):
    pass


class CouponAlreadyUsedError(Exception):
    pass


class CouponService:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository

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
            CouponInvalidError: If the coupon does not exist.
            CouponExpiredError: If the coupon has expired.
            CouponAlreadyUsedError: If the user has already used the coupon.
        """
        coupon = self.coupon_repository.get_by_code(code)

        if not coupon:
            raise CouponInvalidError("Coupon does not exist.")

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
