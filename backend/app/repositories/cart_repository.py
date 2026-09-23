from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from sqlalchemy.orm import joinedload

class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> Cart | None:
        return self.db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == user_id).first()

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

