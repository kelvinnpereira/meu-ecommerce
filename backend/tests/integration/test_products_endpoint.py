from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product


def test_list_products_empty(client: TestClient):
    # Act
    response = client.get("/api/v1/products")

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_list_products_with_data(client: TestClient, db_session: Session):
    # Arrange
    product_1 = Product(
        name="Teclado Mecânico", description="Switches Blue", price=350.00, stock=30
    )
    product_2 = Product(
        name="Mouse Sem Fio", description="Ergonômico", price=150.75, stock=50
    )
    db_session.add(product_1)
    db_session.add(product_2)
    db_session.commit()

    # Act
    response = client.get("/api/v1/products")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["name"] == "Teclado Mecânico"
    assert data[1]["name"] == "Mouse Sem Fio"
