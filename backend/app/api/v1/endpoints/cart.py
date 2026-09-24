from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.schemas.coupon import CouponApply
from app.services.cart_service import (
    CartEmptyError,
    CartItemNotFoundError,
    CartService,
    InsufficientStockError,
    InvalidTransitionError,
    ProductNotFoundError,
)
from app.services.coupon_service import InvalidCouponError

router = APIRouter()


@router.get("", response_model=CartRead)
@router.get("/", response_model=CartRead)
def read_cart(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Retrieve the user's current cart.
    """
    return cart_service.get_or_create_cart(user_id=user_id)


@router.post("", response_model=CartRead)
@router.post("/", response_model=CartRead)
def create_cart(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Explicitly create a new cart (RF-001).
    """
    return cart_service.create_cart(user_id=user_id)


@router.post("/items", response_model=CartRead)
def add_item_to_cart(
    item_data: CartItemCreate,
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Add an item to the cart.
    """
    try:
        return cart_service.add_item(
            user_id=user_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )
    except (InsufficientStockError, ProductNotFoundError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/items/{product_id}", response_model=CartRead)
def update_cart_item_quantity(
    product_id: str,
    item_data: CartItemUpdate,
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Update the quantity of an item in the cart. If quantity is 0, the item is removed.
    """
    try:
        return cart_service.update_item(
            user_id=user_id, product_id=product_id, quantity=item_data.quantity
        )
    except (InsufficientStockError, ProductNotFoundError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CartItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/items/{product_id}", response_model=CartRead)
def remove_item_from_cart(
    product_id: str,
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Remove an item from the cart.
    """
    try:
        return cart_service.remove_item(user_id=user_id, product_id=product_id)
    except CartItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/coupon", response_model=CartRead)
def apply_coupon_to_cart(
    coupon_data: CouponApply,
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Apply a coupon to the cart.
    """
    try:
        return cart_service.apply_coupon(
            user_id=user_id, coupon_code=coupon_data.coupon_code
        )
    except (InvalidCouponError, CartEmptyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/coupon", response_model=CartRead)
def remove_coupon_from_cart(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Remove the coupon from the cart.
    """
    try:
        return cart_service.remove_coupon(user_id=user_id)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/checkout", response_model=CartRead)
def start_checkout(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Move the cart to the 'IN_CHECKOUT' state.
    """
    try:
        return cart_service.start_checkout(user_id=user_id)
    except CartEmptyError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/checkout", response_model=CartRead)
def return_to_editing(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Return the cart from 'IN_CHECKOUT' to 'WITH_ITEMS' state.
    """
    try:
        return cart_service.return_to_cart(user_id=user_id)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/confirm")
def confirm_order(
    user_id: str = Depends(deps.get_user_id),
    cart_service: CartService = Depends(deps.get_cart_service),  # noqa: B008
):
    """
    Confirm the order, creating an order and decrementing stock.
    """
    try:
        confirmed_cart = cart_service.confirm_order(user_id=user_id)
        return {
            "message": "Order confirmed successfully!",
            "cart_status": confirmed_cart.status.value,
        }
    except (InsufficientStockError, CartEmptyError, InvalidCouponError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
