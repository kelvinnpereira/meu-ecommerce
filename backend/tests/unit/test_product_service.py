from unittest.mock import MagicMock, patch

import pytest

from app.models.product import Product
from app.services.product_service import ProductService


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def product_service(mock_db_session, mock_repository):
    with patch(
        "app.services.product_service.ProductRepository",
        return_value=mock_repository,
    ):
        service = ProductService(db=mock_db_session)
        service.repository = mock_repository
        return service


def test_get_all_products(product_service, mock_repository):
    expected_products = [
        Product(id=1, name="Laptop", description="A good one", price=1200.0, stock=10),
        Product(
            id=2, name="Mouse", description="A wireless one", price=50.0, stock=100
        ),
    ]
    mock_repository.list_all.return_value = expected_products

    result = product_service.get_all_products()

    assert result == expected_products
    mock_repository.list_all.assert_called_once()


def test_get_product_by_id_success(product_service, mock_repository):
    expected_product = Product(id=1, name="Laptop", price=1200.0, stock=10)
    mock_repository.get_by_id.return_value = expected_product

    result = product_service.get_product_by_id(1)

    assert result == expected_product
    mock_repository.get_by_id.assert_called_once_with(1)


def test_get_product_by_id_not_found_raises_value_error(
    product_service, mock_repository
):
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Product with id 99 not found"):
        product_service.get_product_by_id(99)


def test_get_product_by_id_for_update_success(product_service, mock_repository):
    expected_product = Product(id=1, name="Laptop", price=1200.0, stock=10)
    mock_repository.get_by_id_for_update.return_value = expected_product

    result = product_service.get_product_by_id_for_update(1)

    assert result == expected_product
    mock_repository.get_by_id_for_update.assert_called_once_with(1)


def test_get_product_by_id_for_update_not_found_raises_value_error(
    product_service, mock_repository
):
    mock_repository.get_by_id_for_update.return_value = None

    with pytest.raises(ValueError, match="Product with id 99 not found for update"):
        product_service.get_product_by_id_for_update(99)


def test_decrement_stock_success(product_service, mock_repository):
    product = Product(id=1, name="Laptop", price=1200.0, stock=10)
    mock_repository.get_by_id_for_update.return_value = product

    product_service.decrement_stock(1, 4)

    assert product.stock == 6


def test_decrement_stock_insufficient_stock_raises_value_error(
    product_service, mock_repository
):
    product = Product(id=1, name="Laptop", price=1200.0, stock=3)
    mock_repository.get_by_id_for_update.return_value = product

    with pytest.raises(ValueError, match="Insufficient stock to decrement."):
        product_service.decrement_stock(1, 5)
