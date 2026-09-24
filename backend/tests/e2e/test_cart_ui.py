import re

from playwright.sync_api import Page, expect

# Define locators for easier access and maintenance
PRODUCTS = "#products-container"
CART = "#cart-section"


def get_product_by_name(page: Page, name: str):
    return page.locator(f".product:has-text('{name}')")


def get_cart_item_by_name(page: Page, name: str):
    return page.locator(f".cart-item:has-text('{name}')")


def test_cart_full_e2e_flow(page: Page):
    """
    Tests the full user flow for the shopping cart:
    1. Add items to the cart.
    2. Verify initial totals.
    3. Update item quantity.
    4. Verify updated totals.
    5. Apply a valid coupon.
    6. Verify discount is applied.
    7. Remove an item.
    8. Verify final totals.
    """
    # 1. Arrange & Navigate
    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    mouse_product = get_product_by_name(page, "Mouse Sem Fio Ergonômico")

    subtotal_loc = page.locator("#cart-subtotal")
    discount_loc = page.locator("#cart-discount")
    total_loc = page.locator("#cart-total")

    # 2. Add Laptop to cart and verify
    laptop_product.locator(".add-to-cart-btn").click()

    cart_item = get_cart_item_by_name(page, "Laptop Moderno")
    expect(cart_item).to_be_visible(timeout=5000)  # Wait for item to appear
    expect(subtotal_loc).to_have_text("R$ 4.500,00")
    expect(total_loc).to_have_text("R$ 4.500,00")

    # 3. Add Mouse to cart and verify
    mouse_product.locator(".add-to-cart-btn").click()

    expect(get_cart_item_by_name(page, "Mouse Sem Fio Ergonômico")).to_be_visible()
    expect(subtotal_loc).to_have_text("R$ 4.650,00")
    expect(total_loc).to_have_text("R$ 4.650,00")

    # 4. Update Laptop quantity to 2
    laptop_cart_item = get_cart_item_by_name(page, "Laptop Moderno")
    laptop_cart_item.locator(".item-quantity").fill("2")
    # After filling, we might need to wait for the AJAX call and re-render
    # The expect calls will implicitly wait
    expect(subtotal_loc).to_have_text("R$ 9.150,00", timeout=5000)
    expect(total_loc).to_have_text("R$ 9.150,00")

    # 5. Apply coupon "SALE10"
    page.locator("#coupon-code").fill("SALE10")
    page.locator("#apply-coupon-btn").click()

    # The discount for 10% of 9150 should be 915.00
    # The new total should be 8235.00
    expect(discount_loc).to_have_text(re.compile(r"-\s*R\$\s*915,00"))
    expect(total_loc).to_have_text("R$ 8.235,00")
    expect(page.locator("#applied-coupon-info")).to_be_visible()

    # 6. Remove Mouse from cart
    mouse_cart_item = get_cart_item_by_name(page, "Mouse Sem Fio Ergonômico")
    mouse_cart_item.locator(".remove-item-btn").click()

    # Cart should re-calculate. Subtotal is now 9000 (2 laptops)
    # Discount is 900 (10% of 9000)
    # Total is 8100
    expect(mouse_cart_item).not_to_be_visible()
    expect(subtotal_loc).to_have_text("R$ 9.000,00")
    expect(discount_loc).to_have_text(re.compile(r"-\s*R\$\s*900,00"))
    expect(total_loc).to_have_text("R$ 8.100,00")


def test_decrease_quantity_to_zero_removes_item(page: Page):
    """
    Tests that decreasing an item's quantity to 0 removes it from the cart
    without triggering a 404 error from concurrent requests or re-render events.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    # Add laptop and teclado to cart
    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    teclado_product = get_product_by_name(page, "Teclado Mecânico RGB")
    teclado_product.locator(".add-to-cart-btn").click()
    teclado_cart_item = get_cart_item_by_name(page, "Teclado Mecânico RGB")
    expect(teclado_cart_item).to_be_visible(timeout=5000)

    # Decrease teclado quantity to 0 and trigger input + blur/change
    qty_input = teclado_cart_item.locator(".item-quantity")
    qty_input.fill("0")
    qty_input.blur()

    # Teclado should be removed, laptop still visible, total updated to laptop price
    expect(teclado_cart_item).not_to_be_visible(timeout=5000)
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible()
    expect(page.locator("#cart-total")).to_have_text("R$ 4.500,00")
    assert len(alerts) == 0, f"Unexpected alert shown: {alerts}"
