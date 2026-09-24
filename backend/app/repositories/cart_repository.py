from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        return (
            self.db.query(Cart)
            .options(joinedload(Cart.items), joinedload(Cart.coupon))
            .filter(Cart.user_id == user_id)
            .order_by(Cart.id.desc())
            .first()
        )

    def create(self, user_id: str) -> Cart:
        db_cart = Cart(user_id=user_id)
        self.db.add(db_cart)
        self.db.commit()
        self.db.refresh(db_cart)
        return db_cart

    def add_item(self, cart: Cart, item: CartItemCreate, unit_price: float) -> Cart:
        # This is a simplified version. The service layer will have more logic.
        db_item = CartItem(**item.dict(), cart_id=cart.id, unit_price=unit_price)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(cart)
        return cart
