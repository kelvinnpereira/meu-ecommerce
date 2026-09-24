from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from app.models.coupon import CouponDiscountType


# Coupon Schemas (for embedding in CartRead)
class CouponRead(BaseModel):
    id: int
    code: str
    discount_type: CouponDiscountType
    value: Decimal

    class Config:
        from_attributes = True
        orm_mode = True


# Cart Item Schemas
class CartItemBase(BaseModel):
    product_id: str = Field(..., pattern=r"^\d+$", max_length=20)
    quantity: int = Field(..., gt=0, le=9999)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=9999)


class CartItemRead(CartItemBase):
    id: int
    unit_price: Decimal

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    class Config:
        from_attributes = True
        orm_mode = True


# Cart Schemas
class CartBase(BaseModel):
    user_id: str


class CartRead(CartBase):
    id: int
    status: str
    items: List[CartItemRead] = []
    coupon: Optional[CouponRead] = None

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Calculates the total price of all items in the cart."""
        if not self.items:
            return Decimal("0.00")
        return sum(item.subtotal for item in self.items)

    @computed_field
    @property
    def discount(self) -> Decimal:
        """Calculates the discount based on the applied coupon."""
        if not self.coupon or not self.items:
            return Decimal("0.00")

        discount_value = Decimal("0.00")
        if self.coupon.discount_type == CouponDiscountType.PERCENTAGE:
            discount_value = self.subtotal * (self.coupon.value / 100)
        elif self.coupon.discount_type == CouponDiscountType.FIXED_VALUE:
            # The discount cannot be greater than the subtotal
            discount_value = min(self.subtotal, self.coupon.value)

        return round(discount_value, 2)

    @computed_field
    @property
    def total(self) -> Decimal:
        """Calculates the final price after discount."""
        final_total = self.subtotal - self.discount
        # The total can't be negative
        return max(Decimal("0.00"), final_total)

    class Config:
        from_attributes = True
        orm_mode = True
