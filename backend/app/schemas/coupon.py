import datetime

from pydantic import BaseModel


# Coupon Schemas
class CouponBase(BaseModel):
    code: str
    discount_type: str
    value: float


class CouponCreate(CouponBase):
    expires_at: datetime.datetime


class CouponRead(CouponBase):
    id: int
    expires_at: datetime.datetime

    class Config:
        orm_mode = True


class CouponApply(BaseModel):
    coupon_code: str
