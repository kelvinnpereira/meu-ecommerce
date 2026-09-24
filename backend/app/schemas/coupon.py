import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    coupon_code: str = Field(..., max_length=50)

    @field_validator("coupon_code")
    @classmethod
    def sanitize_coupon_code(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Coupon code cannot be empty")
        if len(stripped) > 50:
            raise ValueError("Coupon code is too long")
        return stripped
