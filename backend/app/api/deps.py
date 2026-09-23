from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.cart_service import CartService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header missing")
    return user_id


def get_cart_service(db: Session = Depends(get_db)) -> CartService:  # noqa: B008
    return CartService(db)
