from sqlalchemy.orm import Session
from app.models.product import Product
from typing import List


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> List[Product]:
        return self.db.query(Product).all()

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()
