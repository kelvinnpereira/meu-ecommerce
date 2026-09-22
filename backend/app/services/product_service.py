from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.product import Product
from typing import List


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def get_all_products(self) -> List[Product]:
        return self.repository.list_all()
