from typing import ClassVar, Dict, List

from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem, CartStatusEnum
from app.repositories.cart_repository import CartRepository
from app.repositories.coupon_repository import CouponRepository
from app.services.coupon_service import CouponService, InvalidCouponError
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


class InvalidTransitionError(Exception):
    def __init__(self, from_state: CartStatusEnum, to_state: CartStatusEnum):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition from state '{from_state.value}' to '{to_state.value}'."
        )


class CartService:
    _TRANSITIONS: ClassVar[Dict[CartStatusEnum, List[CartStatusEnum]]] = {
        CartStatusEnum.EMPTY: [CartStatusEnum.WITH_ITEMS, CartStatusEnum.ABANDONED],
        CartStatusEnum.WITH_ITEMS: [
            CartStatusEnum.EMPTY,
            CartStatusEnum.IN_CHECKOUT,
            CartStatusEnum.ABANDONED,
        ],
        CartStatusEnum.IN_CHECKOUT: [
            CartStatusEnum.WITH_ITEMS,
            CartStatusEnum.ORDER_CREATED,
            CartStatusEnum.ABANDONED,
        ],
        # ORDER_CREATED and ABANDONED are terminal states.
        CartStatusEnum.ORDER_CREATED: [],
        CartStatusEnum.ABANDONED: [],
    }

    def __init__(self, db: Session):
        self.cart_repository = CartRepository(db)
        self.product_service = ProductService(db)
        self.coupon_service = CouponService(CouponRepository(db))
        self.db = db

    def _change_cart_status(self, cart: Cart, new_status: CartStatusEnum):
        """Validates and executes a cart status transition."""
        current_status = cart.status
        allowed_transitions = self._TRANSITIONS.get(current_status, [])

        # A transition to the same state is always allowed and does nothing.
        if new_status == current_status:
            return

        if new_status not in allowed_transitions:
            raise InvalidTransitionError(from_state=current_status, to_state=new_status)

        cart.status = new_status
        # The session is committed by the calling public method.

    def get_or_create_cart(self, user_id: str) -> Cart:
        """T-005: Gets an existing cart or creates a new one for the user."""
        cart = self.cart_repository.get_by_user_id(user_id)
        if not cart:
            cart = self.cart_repository.create(user_id)
        return cart

    def create_cart(self, user_id: str) -> Cart:
        """RF-001: Explicitly creates a new cart for the user."""
        return self.cart_repository.create(user_id)

    def add_item(self, user_id: str, product_id: str, quantity: int) -> Cart:
        """T-006: Adds an item to the cart, validating stock and product existence."""
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        cart = self.get_or_create_cart(user_id)

        # It is forbidden to add items to a cart that has already been converted to an order or is in checkout
        if cart.status in [CartStatusEnum.ORDER_CREATED, CartStatusEnum.IN_CHECKOUT]:
            raise InvalidTransitionError(cart.status, cart.status)

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

        self._change_cart_status(cart, CartStatusEnum.WITH_ITEMS)

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
        if cart.status in [CartStatusEnum.ORDER_CREATED, CartStatusEnum.IN_CHECKOUT]:
            raise InvalidTransitionError(cart.status, cart.status)

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
        if cart.status in [CartStatusEnum.ORDER_CREATED, CartStatusEnum.IN_CHECKOUT]:
            raise InvalidTransitionError(cart.status, cart.status)

        item_to_remove = next(
            (item for item in cart.items if item.product_id == product_id), None
        )

        if not item_to_remove:
            raise CartItemNotFoundError(product_id)

        # Modify the in-memory list first
        cart.items.remove(item_to_remove)
        # Then, mark for deletion in the session
        self.db.delete(item_to_remove)

        if not cart.items:
            self._change_cart_status(cart, CartStatusEnum.EMPTY)
            cart.coupon_id = None  # Remove coupon if cart becomes empty

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def apply_coupon(self, user_id: str, coupon_code: str) -> Cart:
        """T-010: Validates and applies a coupon to the cart."""
        cart = self.get_or_create_cart(user_id)

        if cart.status == CartStatusEnum.EMPTY:
            raise CartEmptyError("Cannot apply a coupon to an empty cart.")
        if cart.status in [CartStatusEnum.ORDER_CREATED, CartStatusEnum.IN_CHECKOUT]:
            raise InvalidTransitionError(cart.status, cart.status)

        # The service will raise an exception if the coupon is invalid
        validated_coupon = self.coupon_service.validate_coupon(coupon_code, user_id)

        cart.coupon_id = validated_coupon.id

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def remove_coupon(self, user_id: str) -> Cart:
        """T-010: Removes a coupon from the cart."""
        cart = self.get_or_create_cart(user_id)
        if cart.status in [CartStatusEnum.ORDER_CREATED, CartStatusEnum.IN_CHECKOUT]:
            raise InvalidTransitionError(cart.status, cart.status)

        if cart.coupon_id is None:
            # Nothing to do, but it's not an error.
            return cart

        cart.coupon_id = None
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def start_checkout(self, user_id: str) -> Cart:
        """T-011: Transitions the cart to the 'IN_CHECKOUT' state."""
        cart = self.get_or_create_cart(user_id)
        if not cart.items:
            raise CartEmptyError("Cannot start checkout with an empty cart.")

        self._change_cart_status(cart, CartStatusEnum.IN_CHECKOUT)

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def return_to_cart(self, user_id: str) -> Cart:
        """T-011: Returns the cart from 'IN_CHECKOUT' to 'WITH_ITEMS' state for editing."""
        cart = self.get_or_create_cart(user_id)
        if cart.status != CartStatusEnum.IN_CHECKOUT:
            raise InvalidTransitionError(cart.status, CartStatusEnum.WITH_ITEMS)

        self._change_cart_status(cart, CartStatusEnum.WITH_ITEMS)

        self.db.commit()
        self.db.refresh(cart)
        return cart

    def confirm_order(self, user_id: str) -> Cart:
        """
        T-012: Confirms the order, performs an atomic stock check and decrement,
        and transitions the cart to 'ORDER_CREATED'.
        """
        cart = self.get_or_create_cart(user_id)

        # We must be in checkout to confirm an order
        if cart.status != CartStatusEnum.IN_CHECKOUT:
            raise InvalidTransitionError(cart.status, CartStatusEnum.ORDER_CREATED)

        if not cart.items:
            raise CartEmptyError("Cannot confirm an order with an empty cart.")

        # --- Atomic Transaction Block ---
        try:
            # Sort items by product_id to ensure deterministic lock acquisition and prevent deadlocks
            sorted_items = sorted(cart.items, key=lambda item: int(item.product_id))

            # Lock products and check stock
            products_to_update = []
            for item in sorted_items:
                product = self.product_service.get_product_by_id_for_update(
                    int(item.product_id)
                )
                if product.stock < item.quantity:
                    raise InsufficientStockError(
                        item.product_id, item.quantity, product.stock
                    )
                products_to_update.append((product, item.quantity))

            # If all checks pass, decrement stock on the already locked products
            for product, quantity in products_to_update:
                product.stock -= quantity

            # Mark coupon as used if applicable
            if cart.coupon_id:
                self.coupon_service.mark_coupon_as_used(
                    cart.coupon_id, user_id, "some_order_id"
                )

            # Create the order (out of scope for this service, but this is where it would happen)
            # order = self.order_service.create_from_cart(cart)

            # Transition cart status
            self._change_cart_status(cart, CartStatusEnum.ORDER_CREATED)

            self.db.commit()

        except (InsufficientStockError, InvalidCouponError):
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise
        # --- End of Atomic Transaction Block ---

        self.db.refresh(cart)
        return cart

    def abandon_cart(self, user_id: str) -> Cart:
        """Transitions the cart to the 'ABANDONED' state."""
        cart = self.get_or_create_cart(user_id)
        self._change_cart_status(cart, CartStatusEnum.ABANDONED)
        self.db.commit()
        self.db.refresh(cart)
        return cart
