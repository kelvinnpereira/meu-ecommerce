from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, UserCouponUsage
from app.schemas.coupon import CouponCreate


class CouponRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> Optional[Coupon]:
        return (
            self.db.query(Coupon)
            .filter(func.upper(Coupon.code) == func.upper(code.strip()))
            .first()
        )

    def get_usage_by_user_and_coupon(
        self, user_id: str, coupon_id: int
    ) -> Optional[UserCouponUsage]:
        return (
            self.db.query(UserCouponUsage)
            .filter(
                UserCouponUsage.user_id == user_id,
                UserCouponUsage.coupon_id == coupon_id,
            )
            .first()
        )

    def create(self, coupon: CouponCreate) -> Coupon:
        db_coupon = Coupon(**coupon.dict())
        self.db.add(db_coupon)
        self.db.commit()
        self.db.refresh(db_coupon)
        return db_coupon

    def create_usage(
        self, user_id: str, coupon_id: int, order_id: str
    ) -> UserCouponUsage:
        db_usage = UserCouponUsage(
            user_id=user_id, coupon_id=coupon_id, order_id=order_id
        )
        self.db.add(db_usage)
        return db_usage
