import unittest
from unittest.mock import MagicMock, patch

from app.models.product import Product
from app.services.product_service import ProductService


class TestProductService(unittest.TestCase):
    def test_get_all_products(self):
        # Arrange
        mock_db_session = MagicMock()
        mock_repository = MagicMock()

        expected_products = [
            Product(
                id=1, name="Laptop", description="A good one", price=1200.0, stock=10
            ),
            Product(
                id=2, name="Mouse", description="A wireless one", price=50.0, stock=100
            ),
        ]
        mock_repository.list_all.return_value = expected_products

        with patch(
            "app.services.product_service.ProductRepository",
            return_value=mock_repository,
        ):
            service = ProductService(db=mock_db_session)

            # Act
            result = service.get_all_products()

            # Assert
            self.assertEqual(result, expected_products)
            mock_repository.list_all.assert_called_once()


if __name__ == "__main__":
    unittest.main()
