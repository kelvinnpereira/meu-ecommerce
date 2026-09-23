from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem, CartStatusEnum
from app.repositories.cart_repository import CartRepository
from app.repositories.coupon_repository import CouponRepository
from app.services.coupon_service import CouponService
from app.services.product_service import ProductService


class InsufficientStockError(Exception):
    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}. Requested: {requested}, Available: {available}"
        )


class ProductNotFoundError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product with id {product_id} not found.")


class CartItemNotFoundError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Item with product id {product_id} not found in cart.")


class CartEmptyError(Exception):
    def __init__(self, message="Cannot perform this operation on an empty cart."):
        self.message = message
        super().__init__(self.message)


class CartService:
    def __init__(self, db: Session):
        self.cart_repository = CartRepository(db)
        self.product_service = ProductService(db)
        self.coupon_service = CouponService(CouponRepository(db))
        self.db = db

    def get_or_create_cart(self, user_id: str) -> Cart:
        """T-005: Gets an existing cart or creates a new one for the user."""
        cart = self.cart_repository.get_by_user_id(user_id)
        if not cart:
            cart = self.cart_repository.create(user_id)
        return cart

    def add_item(self, user_id: str, product_id: str, quantity: int) -> Cart:
        """T-006: Adds an item to the cart, validating stock and product existence."""
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        cart = self.get_or_create_cart(user_id)

        try:
            product = self.product_service.get_product_by_id(int(product_id))
        except ValueError:
            raise ProductNotFoundError(product_id)

        item_in_cart = next(
            (item for item in cart.items if item.product_id == product_id), None
        )

        requested_quantity = quantity
        if item_in_cart:
            requested_quantity += item_in_cart.quantity

        if product.stock < requested_quantity:
            raise InsufficientStockError(product_id, requested_quantity, product.stock)

        if item_in_cart:
            item_in_cart.quantity += quantity
        else:
            new_item = CartItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
                cart_id=cart.id,
            )
            self.db.add(new_item)

        if cart.status == CartStatusEnum.EMPTY:
            cart.status = CartStatusEnum.WITH_ITEMS

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def update_item(self, user_id: str, product_id: str, quantity: int) -> Cart:
        """T-007: Updates an item's quantity or removes it if quantity is 0."""
        if quantity < 0:
            raise ValueError("Quantity must be a non-negative integer.")

        if quantity == 0:
            return self.remove_item(user_id, product_id)

        cart = self.get_or_create_cart(user_id)
        item_in_cart = next(
            (item for item in cart.items if item.product_id == product_id), None
        )

        if not item_in_cart:
            raise CartItemNotFoundError(product_id)

        try:
            product = self.product_service.get_product_by_id(int(product_id))
        except ValueError:
            raise ProductNotFoundError(product_id)

        if product.stock < quantity:
            raise InsufficientStockError(product_id, quantity, product.stock)

        item_in_cart.quantity = quantity
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def remove_item(self, user_id: str, product_id: str) -> Cart:
        """T-007: Removes an item from the cart."""
        cart = self.get_or_create_cart(user_id)
        item_to_remove = next(
            (item for item in cart.items if item.product_id == product_id), None
        )

        if not item_to_remove:
            raise CartItemNotFoundError(product_id)

        cart.items.remove(item_to_remove)
        self.db.delete(item_to_remove)

        if not cart.items:
            cart.status = CartStatusEnum.EMPTY
            cart.coupon_id = None  # Remove coupon if cart becomes empty

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def apply_coupon(self, user_id: str, coupon_code: str) -> Cart:
        """T-010: Validates and applies a coupon to the cart."""
        cart = self.get_or_create_cart(user_id)

        if cart.status == CartStatusEnum.EMPTY:
            raise CartEmptyError("Cannot apply a coupon to an empty cart.")

        # The service will raise an exception if the coupon is invalid
        validated_coupon = self.coupon_service.validate_coupon(coupon_code, user_id)

        cart.coupon_id = validated_coupon.id

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def remove_coupon(self, user_id: str) -> Cart:
        """T-010: Removes a coupon from the cart."""
        cart = self.get_or_create_cart(user_id)

        if cart.coupon_id is None:
            # Nothing to do, but it's not an error.
            return cart

        cart.coupon_id = None
        self.db.commit()
        self.db.refresh(cart)
        return cart
