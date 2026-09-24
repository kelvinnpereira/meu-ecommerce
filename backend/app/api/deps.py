import re

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.cart_service import CartService

USER_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header missing")
    user_id = user_id.strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header missing")
    if not USER_ID_REGEX.match(user_id):
        raise HTTPException(status_code=400, detail="Invalid X-User-ID header")
    return user_id


def get_cart_service(db: Session = Depends(get_db)) -> CartService:  # noqa: B008
    return CartService(db)
