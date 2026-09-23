import enum
from sqlalchemy import Column, Integer, String, Enum, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class CartStatusEnum(str, enum.Enum):
    EMPTY = "EMPTY"
    WITH_ITEMS = "WITH_ITEMS"
    IN_CHECKOUT = "IN_CHECKOUT"
    ORDER_CREATED = "ORDER_CREATED"
    ABANDONED = "ABANDONED"

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(CartStatusEnum), default=CartStatusEnum.EMPTY, nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    coupon = relationship("Coupon")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    cart = relationship("Cart", back_populates="items")
