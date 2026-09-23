from typing import List

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)
        self.db = db

    def get_all_products(self) -> List[Product]:
        return self.repository.list_all()

    def get_product_by_id(self, product_id: int) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        return product

    def get_product_by_id_for_update(self, product_id: int) -> Product:
        """
        Retrieves a product by its ID with a row-level lock, to be used in transactions.
        """
        product = self.repository.get_by_id_for_update(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found for update")
        return product

    def decrement_stock(self, product_id: int, quantity: int):
        """
        Decrements the stock for a given product.
        This method assumes the product is already locked by the transaction.
        """
        product = self.get_product_by_id_for_update(product_id)
        if product.stock < quantity:
            # This should be caught by the service layer's initial check,
            # but it's here as a safeguard.
            raise ValueError("Insufficient stock to decrement.")
        product.stock -= quantity
        # The commit is handled by the calling service that manages the transaction.
