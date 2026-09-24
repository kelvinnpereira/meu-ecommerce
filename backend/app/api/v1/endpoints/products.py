from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.product import Product
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/products", response_model=List[Product])
async def list_products(db: Session = Depends(deps.get_db)):  # noqa: B008
    service = ProductService(db)
    return service.get_all_products()
