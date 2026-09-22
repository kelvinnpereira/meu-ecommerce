from playwright.sync_api import Page, expect


def test_product_listing_e2e(page: Page):
    # Arrange
    # The seeded data should be available
    seeded_products = [
        "Laptop Moderno",
        "Mouse Sem Fio Ergonômico",
        "Teclado Mecânico RGB",
    ]

    # Act
    # Navigate to the frontend application
    page.goto("http://frontend")

    # Assert
    # Check that the main heading is visible
    expect(page.locator("h1")).to_have_text("Produtos")

    # Wait for the loading indicator to disappear
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    # Check that the product container is visible
    products_container = page.locator("#products-container")
    expect(products_container).to_be_visible()

    # Check that all seeded products are rendered on the page
    for product_name in seeded_products:
        product_card = products_container.locator(
            f".product-card:has-text('{product_name}')"
        )
        expect(product_card).to_be_visible()
        print(f"Found product: {product_name}")

    # Optional: Check a specific detail for one product
    laptop_card = products_container.locator(".product-card:has-text('Laptop Moderno')")
    expect(laptop_card.locator("p:has-text('Preço: R$ 4500.00')")).to_be_visible()
