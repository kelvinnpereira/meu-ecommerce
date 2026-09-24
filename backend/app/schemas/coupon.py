import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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

    model_config = ConfigDict(from_attributes=True)


class CouponApply(BaseModel):
    coupon_code: str

    @field_validator("coupon_code")
    @classmethod
    def sanitize_coupon_code(cls, v: str) -> str:
        return v.strip()
