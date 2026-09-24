from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.cart import Cart, CartStatusEnum
from app.models.coupon import Coupon
from app.models.product import Product
from app.services.coupon_service import (
    CouponAlreadyUsedError,
    CouponExpiredError,
    InvalidCouponError,
)


class FakeCartRepository:
    """In-memory Fake implementation of CartRepository."""

    def __init__(self):
        self.carts_by_id: Dict[int, Cart] = {}
        self.carts_by_user: Dict[str, List[Cart]] = {}
        self._next_id = 1

    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        """Returns the most recent cart for the user."""
        user_carts = self.carts_by_user.get(user_id, [])
        return user_carts[-1] if user_carts else None

    def create(self, user_id: str) -> Cart:
        cart = Cart(
            id=self._next_id,
            user_id=user_id,
            status=CartStatusEnum.EMPTY,
            coupon_id=None,
        )
        cart.items = []
        self._next_id += 1
        self.carts_by_id[cart.id] = cart
        if user_id not in self.carts_by_user:
            self.carts_by_user[user_id] = []
        self.carts_by_user[user_id].append(cart)
        return cart


class StubProductService:
    """Stub implementation of ProductService to control product returns and stock checks."""

    def __init__(self, products: Optional[List[Product]] = None):
        self.products: Dict[int, Product] = {}
        if products:
            for p in products:
                self.add_product(p)

    def add_product(self, product: Product):
        self.products[product.id] = product

    def get_all_products(self) -> List[Product]:
        return list(self.products.values())

    def get_product_by_id(self, product_id: int) -> Product:
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        return product

    def get_product_by_id_for_update(self, product_id: int) -> Product:
        return self.get_product_by_id(product_id)

    def decrement_stock(self, product_id: int, quantity: int):
        product = self.get_product_by_id(product_id)
        if product.stock < quantity:
            raise ValueError("Insufficient stock to decrement.")
        product.stock -= quantity


class SpyCouponService:
    """Spy implementation of CouponService to observe calls and control validation."""

    def __init__(self, valid_coupons: Optional[List[Coupon]] = None):
        self.coupons: Dict[str, Coupon] = {}
        self.validated_calls: List[dict] = []
        self.used_calls: List[dict] = []
        self.already_used_users: set = set()

        if valid_coupons:
            for c in valid_coupons:
                self.add_coupon(c)

    def add_coupon(self, coupon: Coupon):
        self.coupons[coupon.code.upper()] = coupon

    def validate_coupon(self, code: str, user_id: str) -> Coupon:
        self.validated_calls.append({"code": code, "user_id": user_id})
        norm_code = code.strip().upper()
        coupon = self.coupons.get(norm_code)
        if not coupon:
            raise InvalidCouponError("Coupon does not exist.")

        now = (
            datetime.now(timezone.utc)
            if coupon.expires_at.tzinfo
            else datetime.now(timezone.utc).replace(tzinfo=None)
        )
        if coupon.expires_at < now:
            raise CouponExpiredError("Coupon has expired.")

        if (user_id, coupon.id) in self.already_used_users:
            raise CouponAlreadyUsedError("Coupon has already been used by this user.")

        return coupon

    def mark_coupon_as_used(self, coupon_id: int, user_id: str, order_id: str):
        self.used_calls.append(
            {"coupon_id": coupon_id, "user_id": user_id, "order_id": order_id}
        )
        self.already_used_users.add((user_id, coupon_id))


class MockDbSession:
    """Mock/Spy of SQLAlchemy Session to verify transactional boundaries and relations."""

    def __init__(self, cart_repository: Optional[FakeCartRepository] = None):
        self.cart_repository = cart_repository
        self.added_items: List = []
        self.deleted_items: List = []
        self.commit_count: int = 0
        self.rollback_count: int = 0
        self.refreshed_items: List = []

    def add(self, item):
        self.added_items.append(item)
        if hasattr(item, "cart_id") and self.cart_repository:
            cart = self.cart_repository.carts_by_id.get(item.cart_id)
            if cart and item not in cart.items:
                cart.items.append(item)

    def delete(self, item):
        self.deleted_items.append(item)
        if hasattr(item, "cart_id") and self.cart_repository:
            cart = self.cart_repository.carts_by_id.get(item.cart_id)
            if cart and item in cart.items:
                cart.items.remove(item)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, item):
        self.refreshed_items.append(item)
