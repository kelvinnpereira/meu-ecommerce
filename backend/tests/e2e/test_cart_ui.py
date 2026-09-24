import re
import sqlite3

from playwright.sync_api import Page, expect

# Define locators for easier access and maintenance
PRODUCTS = "#products-container"
CART = "#cart-section"


def get_product_by_name(page: Page, name: str):
    return page.locator(
        ".product",
        has=page.locator("h3", has_text=re.compile(rf"^\s*{re.escape(name)}\s*$")),
    )


def get_cart_item_by_name(page: Page, name: str):
    return page.locator(
        ".cart-item",
        has=page.locator("strong", has_text=re.compile(rf"^\s*{re.escape(name)}\s*$")),
    )


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


def test_e2e_checkout_and_return_to_cart_flow(page: Page):
    """
    Tests RF-008 and RF-009 on the UI:
    1. Add product to cart.
    2. Click 'Finalizar Compra' -> button changes to 'Confirmar Pedido' and 'Voltar para Edição' appears.
    3. Click 'Voltar para Edição' -> button returns to 'Finalizar Compra' and return button disappears.
    """
    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    checkout_btn = page.locator("#checkout-btn")
    expect(checkout_btn).to_have_text("Finalizar Compra")

    # Click checkout
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)
    return_btn = page.locator("#return-to-cart-btn")
    expect(return_btn).to_be_visible()

    # Click return to cart
    return_btn.click()
    expect(checkout_btn).to_have_text("Finalizar Compra", timeout=5000)
    expect(return_btn).to_be_hidden()


def test_e2e_complete_checkout_and_confirm_order(page: Page):
    """
    Tests RF-010 on the UI:
    1. Add product and apply coupon.
    2. Start checkout.
    3. Confirm order, verifying success dialog and post-order clean state.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    # Apply coupon
    page.locator("#coupon-code").fill("SALE10")
    page.locator("#apply-coupon-btn").click()
    expect(page.locator("#applied-coupon-info")).to_be_visible(timeout=5000)

    # Start checkout
    checkout_btn = page.locator("#checkout-btn")
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)

    # Confirm order
    checkout_btn.click()

    # Wait for confirmation dialog and check message
    page.wait_for_timeout(1000)
    assert any("Order confirmed" in msg or "sucesso" in msg.lower() for msg in alerts)

    # UI should have reset to an empty cart
    expect(page.locator("#cart-items-container")).to_contain_text(
        "Seu carrinho está vazio.", timeout=5000
    )
    expect(page.locator("#cart-total")).to_have_text("R$ 0,00")
    expect(checkout_btn).to_be_disabled()


def test_e2e_apply_invalid_coupon_shows_alert(page: Page):
    """
    Tests applying an invalid coupon code in the UI shows an alert dialog
    and leaves totals unchanged without discount.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    # Try applying nonexistent coupon
    page.locator("#coupon-code").fill("CUPOM_FALSO_123")
    page.locator("#apply-coupon-btn").click()

    page.wait_for_timeout(1000)
    assert len(alerts) >= 1
    assert (
        "Coupon does not exist" in alerts[0]
        or "inválido" in alerts[0].lower()
        or "não encontrado" in alerts[0].lower()
    )
    expect(page.locator("#applied-coupon-info")).to_be_hidden()
    expect(page.locator("#cart-total")).to_have_text("R$ 4.500,00")


def test_e2e_remove_all_items_clears_coupon_and_resets_ui(page: Page):
    """
    Tests RF-004 on the UI:
    Removing all items from the cart resets UI, removes applied coupon and disables checkout.
    """
    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    page.locator("#coupon-code").fill("SALE10")
    page.locator("#apply-coupon-btn").click()
    expect(page.locator("#applied-coupon-info")).to_be_visible(timeout=5000)

    # Remove the only item in the cart
    cart_item = get_cart_item_by_name(page, "Laptop Moderno")
    cart_item.locator(".remove-item-btn").click()

    expect(cart_item).not_to_be_visible(timeout=5000)
    expect(page.locator("#cart-items-container")).to_contain_text(
        "Seu carrinho está vazio."
    )
    expect(page.locator("#applied-coupon-info")).to_be_hidden()
    expect(page.locator("#coupon-form")).to_be_visible()
    expect(page.locator("#checkout-btn")).to_be_disabled()


def test_e2e_ui_full_purchase_verifies_db_persistence(page: Page):
    """
    Fluxo 1 (UI + Banco E2E):
    - Executa compra completa pela interface do usuário.
    - Valida feedback visual no frontend.
    - Valida diretamente a persistência no SQLite (ecommerce.db):
      * Estoques decrementados.
      * Registro em user_coupon_usages.
      * Carrinho no estado ORDER_CREATED.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    # Adicionar 1 Laptop Moderno
    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    # Adicionar 1 Mouse Sem Fio Ergonômico
    mouse_product = get_product_by_name(page, "Mouse Sem Fio Ergonômico")
    mouse_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Mouse Sem Fio Ergonômico")).to_be_visible(
        timeout=5000
    )

    # Aplicar cupom SALE10 (10%)
    page.locator("#coupon-code").fill("SALE10")
    page.locator("#apply-coupon-btn").click()
    expect(page.locator("#applied-coupon-info")).to_be_visible(timeout=5000)

    # Subtotal 4650, desconto 465, total 4185
    expect(page.locator("#cart-subtotal")).to_have_text("R$ 4.650,00")
    expect(page.locator("#cart-total")).to_have_text("R$ 4.185,00")

    # Iniciar checkout
    checkout_btn = page.locator("#checkout-btn")
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)

    # Confirmar pedido
    checkout_btn.click()
    page.wait_for_timeout(1000)

    # Verificar alerta de sucesso
    assert any("sucesso" in msg.lower() or "confirmed" in msg.lower() for msg in alerts)

    # Verificar que o carrinho resetou na UI
    expect(page.locator("#cart-items-container")).to_contain_text(
        "Seu carrinho está vazio.", timeout=5000
    )
    expect(page.locator("#cart-total")).to_have_text("R$ 0,00")
    expect(checkout_btn).to_be_disabled()

    # Validação direta no banco de dados SQLite
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT stock FROM products WHERE name = 'Laptop Moderno'")
    assert cursor.fetchone()["stock"] == 14  # 15 - 1

    cursor.execute("SELECT stock FROM products WHERE name = 'Mouse Sem Fio Ergonômico'")
    assert cursor.fetchone()["stock"] == 49  # 50 - 1

    cursor.execute("SELECT * FROM user_coupon_usages WHERE user_id = 'user-123'")
    assert cursor.fetchone() is not None

    cursor.execute(
        "SELECT status FROM carts WHERE user_id = 'user-123' ORDER BY id DESC"
    )
    # O último carrinho fechado deve estar como ORDER_CREATED
    rows = cursor.fetchall()
    assert any(r["status"] == "ORDER_CREATED" for r in rows)
    conn.close()


def test_e2e_ui_checkout_edit_return_and_completion(page: Page):
    """
    Fluxo 2 (UI + Banco E2E):
    - Adiciona 1 Teclado Mecânico RGB.
    - Entra em checkout ('Finalizar Compra').
    - Retorna para edição ('Voltar para Edição').
    - Altera quantidade de Teclado para 2 unidades.
    - Adiciona 1 Mouse Sem Fio.
    - Avança para checkout e confirma pedido.
    - Valida que as quantidades atualizadas decrementaram corretamente no banco.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    # Adicionar 1 Teclado Mecânico
    teclado_product = get_product_by_name(page, "Teclado Mecânico RGB")
    teclado_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Teclado Mecânico RGB")).to_be_visible(
        timeout=5000
    )

    # Entrar em checkout
    checkout_btn = page.locator("#checkout-btn")
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)
    return_btn = page.locator("#return-to-cart-btn")
    expect(return_btn).to_be_visible()

    # Voltar para edição
    return_btn.click()
    expect(checkout_btn).to_have_text("Finalizar Compra", timeout=5000)
    expect(return_btn).to_be_hidden()

    # Alterar quantidade de Teclado para 2
    teclado_item = get_cart_item_by_name(page, "Teclado Mecânico RGB")
    teclado_item.locator(".item-quantity").fill("2")
    expect(page.locator("#cart-subtotal")).to_have_text("R$ 700,00", timeout=5000)

    # Adicionar 1 Mouse Sem Fio
    mouse_product = get_product_by_name(page, "Mouse Sem Fio Ergonômico")
    mouse_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Mouse Sem Fio Ergonômico")).to_be_visible(
        timeout=5000
    )
    expect(page.locator("#cart-total")).to_have_text("R$ 850,00", timeout=5000)

    # Avançar para checkout e confirmar pedido
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)
    checkout_btn.click()
    page.wait_for_timeout(1000)

    assert any("sucesso" in msg.lower() or "confirmed" in msg.lower() for msg in alerts)

    # Validação no banco SQLite
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT stock FROM products WHERE name = 'Teclado Mecânico RGB'")
    assert cursor.fetchone()["stock"] == 28  # 30 - 2

    cursor.execute("SELECT stock FROM products WHERE name = 'Mouse Sem Fio Ergonômico'")
    assert cursor.fetchone()["stock"] == 49  # 50 - 1
    conn.close()


def test_e2e_ui_stock_conflict_rollback_and_recovery(page: Page):
    """
    Fluxo 3 (UI + Banco E2E - RN-006 / RN-007):
    - Usuário adiciona 2 unidades de Laptop na UI e entra em checkout.
    - Ação concorrente altera o estoque do produto no banco para 1 unidade.
    - Usuário clica em 'Confirmar Pedido'.
    - UI exibe alerta de erro de estoque.
    - Banco de dados permanece íntegro com rollback total (estoque permanece 1, sem cupom consumido).
    - Usuário clica em 'Voltar para Edição', ajusta quantidade para 1 e conclui com sucesso.
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    laptop_item = get_cart_item_by_name(page, "Laptop Moderno")
    expect(laptop_item).to_be_visible(timeout=5000)

    # Ajustar para 2 unidades
    laptop_item.locator(".item-quantity").fill("2")
    expect(page.locator("#cart-total")).to_have_text("R$ 9.000,00", timeout=5000)

    # Aplicar cupom SALE10
    page.locator("#coupon-code").fill("SALE10")
    page.locator("#apply-coupon-btn").click()
    expect(page.locator("#applied-coupon-info")).to_be_visible(timeout=5000)

    # Entrar em checkout
    checkout_btn = page.locator("#checkout-btn")
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)

    # Ação concorrente: reduzir estoque de Laptop no banco diretamente para 1 unidade
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock = 1 WHERE name = 'Laptop Moderno'")
    conn.commit()
    conn.close()

    # Clicar em Confirmar Pedido com estoque insuficiente
    checkout_btn.click()
    page.wait_for_timeout(1000)

    # Alerta de erro deve ter sido exibido
    assert len(alerts) >= 1
    assert any("stock" in msg.lower() or "estoque" in msg.lower() for msg in alerts)

    # Validação do Rollback Atômico no banco de dados
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE name = 'Laptop Moderno'")
    assert cursor.fetchone()["stock"] == 1  # Não decrementou nem negativou

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM user_coupon_usages WHERE user_id = 'user-123'"
    )
    assert cursor.fetchone()["cnt"] == 0  # Cupom não foi consumido
    conn.close()

    # Recuperação: voltar para edição e ajustar para 1 unidade
    return_btn = page.locator("#return-to-cart-btn")
    return_btn.click()
    expect(checkout_btn).to_have_text("Finalizar Compra", timeout=5000)

    laptop_item = get_cart_item_by_name(page, "Laptop Moderno")
    laptop_item.locator(".item-quantity").fill("1")
    expect(page.locator("#cart-total")).to_have_text("R$ 4.050,00", timeout=5000)

    # Iniciar checkout e confirmar com quantidade ajustada
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)
    checkout_btn.click()
    page.wait_for_timeout(1000)

    # Validação final no banco
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE name = 'Laptop Moderno'")
    assert cursor.fetchone()["stock"] == 0  # Decrementado de 1 para 0

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM user_coupon_usages WHERE user_id = 'user-123'"
    )
    assert cursor.fetchone()["cnt"] == 1
    conn.close()


def test_e2e_ui_coupon_lifecycle_and_reusage_blocked(page: Page):
    """
    Fluxo 4 (UI E2E - RN-001, RN-002, RN-005):
    - Tenta aplicar cupom inexistente e expirado (bloqueados com alerta).
    - Aplica cupom fixo 50FIXO (R$ 50,00).
    - Conclui o pedido com o cupom aplicado.
    - Inicia nova compra com o mesmo usuário e tenta aplicar novamente 50FIXO.
    - Sistema bloqueia nova aplicação informando uso anterior (RN-002).
    """
    alerts = []
    page.on("dialog", lambda dialog: (alerts.append(dialog.message), dialog.accept()))

    page.goto("http://frontend")
    expect(page.locator("h1")).to_have_text("Produtos")
    expect(page.locator("#loading-indicator")).to_be_hidden(timeout=10000)

    laptop_product = get_product_by_name(page, "Laptop Moderno")
    laptop_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Laptop Moderno")).to_be_visible(timeout=5000)

    # 1. Cupom inexistente
    page.locator("#coupon-code").fill("CUPOM_FALSO_123")
    page.locator("#apply-coupon-btn").click()
    page.wait_for_timeout(500)
    assert any(
        "does not exist" in msg.lower() or "inválido" in msg.lower() for msg in alerts
    )
    expect(page.locator("#cart-total")).to_have_text("R$ 4.500,00")

    # 2. Cupom expirado
    page.locator("#coupon-code").fill("EXPIRADO")
    page.locator("#apply-coupon-btn").click()
    page.wait_for_timeout(500)
    assert any("expired" in msg.lower() or "expirado" in msg.lower() for msg in alerts)
    expect(page.locator("#cart-total")).to_have_text("R$ 4.500,00")

    # 3. Cupom fixo válido 50FIXO
    page.locator("#coupon-code").fill("50FIXO")
    page.locator("#apply-coupon-btn").click()
    expect(page.locator("#applied-coupon-info")).to_be_visible(timeout=5000)
    expect(page.locator("#cart-discount")).to_have_text(re.compile(r"-\s*R\$\s*50,00"))
    expect(page.locator("#cart-total")).to_have_text("R$ 4.450,00")

    # 4. Finalizar compra
    checkout_btn = page.locator("#checkout-btn")
    checkout_btn.click()
    expect(checkout_btn).to_have_text("Confirmar Pedido", timeout=5000)
    checkout_btn.click()
    page.wait_for_timeout(1000)

    # 5. Nova compra: adicionar Mouse Sem Fio
    mouse_product = get_product_by_name(page, "Mouse Sem Fio Ergonômico")
    mouse_product.locator(".add-to-cart-btn").click()
    expect(get_cart_item_by_name(page, "Mouse Sem Fio Ergonômico")).to_be_visible(
        timeout=5000
    )
    expect(page.locator("#cart-total")).to_have_text("R$ 150,00")

    # 6. Tentar reutilizar 50FIXO
    alerts.clear()
    page.locator("#coupon-code").fill("50FIXO")
    page.locator("#apply-coupon-btn").click()
    page.wait_for_timeout(500)

    # Alerta deve indicar que o cupom já foi utilizado
    assert len(alerts) >= 1
    assert any(
        "already been used" in msg.lower()
        or "já foi utilizado" in msg.lower()
        or "utilizado" in msg.lower()
        for msg in alerts
    )
    expect(page.locator("#applied-coupon-info")).to_be_hidden()
    expect(page.locator("#cart-total")).to_have_text("R$ 150,00")
