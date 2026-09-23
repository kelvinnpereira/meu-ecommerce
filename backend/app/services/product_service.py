from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from typing import List


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def get_all_products(self) -> List[Product]:
        return self.repository.list_all()

    def get_product_by_id(self, product_id: int) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        return product
