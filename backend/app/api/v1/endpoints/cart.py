from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.cart import CartRead, CartItemCreate, CartItemUpdate
from app.services.cart_service import (
    CartService,
    CartEmptyError,
    CartItemNotFoundError,
    InsufficientStockError,
    InvalidTransitionError,
    ProductNotFoundError,
)
from app.services.coupon_service import (
    CouponAlreadyUsedError,
    CouponExpiredError,
    InvalidCouponError,
)

router = APIRouter()

# This is a simplification for the example.
# In a real app, you'd get the user_id from a proper authentication system.
USER_ID = "user_123"


@router.get("/", response_model=CartRead)
def get_cart(db: Session = Depends(get_db)):
    """
    T-005: Retrieve the current user's cart.
    """
    cart_service = CartService(db)
    cart = cart_service.get_or_create_cart(USER_ID)
    return cart


@router.post("/items", response_model=CartRead)
def add_item_to_cart(item: CartItemCreate, db: Session = Depends(get_db)):
    """
    T-006: Add an item to the cart.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.add_item(
            user_id=USER_ID, product_id=item.product_id, quantity=item.quantity
        )
        return cart
    except (InsufficientStockError, ProductNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/items/{product_id}", response_model=CartRead)
def update_cart_item(
    product_id: str, item: CartItemUpdate, db: Session = Depends(get_db)
):
    """
    T-007: Update an item's quantity in the cart.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.update_item(
            user_id=USER_ID, product_id=product_id, quantity=item.quantity
        )
        return cart
    except (InsufficientStockError, ProductNotFoundError, CartItemNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/items/{product_id}", response_model=CartRead)
def remove_item_from_cart(product_id: str, db: Session = Depends(get_db)):
    """
    T-007: Remove an item from the cart.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.remove_item(user_id=USER_ID, product_id=product_id)
        return cart
    except CartItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/coupon/{coupon_code}", response_model=CartRead)
def apply_coupon_to_cart(coupon_code: str, db: Session = Depends(get_db)):
    """
    T-010: Apply a coupon to the cart.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.apply_coupon(user_id=USER_ID, coupon_code=coupon_code)
        return cart
    except (
        CartEmptyError,
        CouponAlreadyUsedError,
        CouponExpiredError,
        InvalidCouponError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/coupon", response_model=CartRead)
def remove_coupon_from_cart(db: Session = Depends(get_db)):
    """
    T-010: Remove the coupon from the cart.
    """
    cart_service = CartService(db)
    cart = cart_service.remove_coupon(user_id=USER_ID)
    return cart


@router.post("/checkout", response_model=CartRead)
def start_checkout(db: Session = Depends(get_db)):
    """
    T-011: Start the checkout process.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.start_checkout(user_id=USER_ID)
        return cart
    except (CartEmptyError, InvalidTransitionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/return-to-cart", response_model=CartRead)
def return_to_cart(db: Session = Depends(get_db)):
    """
    T-011: Return from checkout to continue shopping.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.return_to_cart(user_id=USER_ID)
        return cart
    except InvalidTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm", response_model=CartRead)
def confirm_order(db: Session = Depends(get_db)):
    """
    T-012: Confirm the order.
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.confirm_order(user_id=USER_ID)
        return cart
    except (
        CartEmptyError,
        InvalidTransitionError,
        InsufficientStockError,
        InvalidCouponError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during order confirmation.",
        )
