import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class CouponDiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_VALUE = "FIXED_VALUE"


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(Enum(CouponDiscountType), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    max_uses_per_user = Column(Integer, default=1)

    usages = relationship("UserCouponUsage", back_populates="coupon")


class UserCouponUsage(Base):
    __tablename__ = "user_coupon_usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    order_id = Column(String, nullable=False)

    coupon = relationship("Coupon", back_populates="usages")
