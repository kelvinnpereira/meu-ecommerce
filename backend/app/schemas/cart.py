from pydantic import BaseModel, Field
from typing import List, Optional

# Cart Item Schemas
class CartItemBase(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemRead(CartItemBase):
    id: int
    unit_price: float
    
    class Config:
        orm_mode = True

# Cart Schemas
class CartBase(BaseModel):
    user_id: str

class CartRead(CartBase):
    id: int
    status: str
    items: List[CartItemRead] = []
    coupon_id: Optional[int] = None

    class Config:
        orm_mode = True
