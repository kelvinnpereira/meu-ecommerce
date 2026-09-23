from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> List[Product]:
        return self.db.query(Product).all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_id_for_update(self, product_id: int) -> Optional[Product]:
        """
        Retrieves a product by its ID with a row-level lock for updating.
        """
        return (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )
