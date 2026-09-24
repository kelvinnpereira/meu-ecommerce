import sqlite3

import requests

BASE_URL = "http://localhost:8000/api/v1"


def get_db():
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    return conn


def test_e2e_api_full_purchase_and_db_state():
    """
    Fluxo 1 (API E2E):
    - user-e2e-a adiciona 1 Laptop e 2 Mouses.
    - Aplica cupom SALE10 (10%).
    - Avança para checkout (IN_CHECKOUT).
    - Confirma pedido (ORDER_CREATED).
    - Valida o estado final diretamente nas tabelas products, carts e user_coupon_usages no SQLite.
    - Garante que novas mutações no carrinho convertido retornam HTTP 409 (RN-009).
    """
    user_id = "user-e2e-a"
    headers = {"X-User-ID": user_id}

    # 1. Obter catálogo de produtos para obter os IDs corretos
    res = requests.get(f"{BASE_URL}/products")
    assert res.status_code == 200
    products = {p["name"]: p for p in res.json()}
    laptop = products["Laptop Moderno"]
    mouse = products["Mouse Sem Fio Ergonômico"]

    laptop_initial_stock = laptop["stock"]
    mouse_initial_stock = mouse["stock"]

    # 2. Adicionar 1 Laptop ao carrinho
    res = requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(laptop["id"]), "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 200
    cart_data = res.json()
    assert cart_data["status"] == "WITH_ITEMS"
    assert len(cart_data["items"]) == 1

    # 3. Adicionar 2 Mouses ao carrinho
    res = requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(mouse["id"]), "quantity": 2},
        headers=headers,
    )
    assert res.status_code == 200
    cart_data = res.json()
    assert len(cart_data["items"]) == 2
    # Laptop: 4500, Mouse: 2 * 150 = 300. Subtotal: 4800
    assert float(cart_data["subtotal"]) == 4800.00
    assert float(cart_data["total"]) == 4800.00

    # 4. Aplicar cupom SALE10 (10%)
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "SALE10"},
        headers=headers,
    )
    assert res.status_code == 200
    cart_data = res.json()
    assert float(cart_data["discount"]) == 480.00
    assert float(cart_data["total"]) == 4320.00

    # 5. Iniciar checkout
    res = requests.post(f"{BASE_URL}/cart/checkout", headers=headers)
    assert res.status_code == 200
    cart_data = res.json()
    assert cart_data["status"] == "IN_CHECKOUT"

    # 6. Confirmar pedido
    res = requests.post(f"{BASE_URL}/cart/confirm", headers=headers)
    assert res.status_code == 200
    confirm_data = res.json()
    assert confirm_data["cart_status"] == "ORDER_CREATED"

    # 7. Validação direta na camada de persistência (ecommerce.db)
    conn = get_db()
    cursor = conn.cursor()

    # Estoques decrementados atomicamente
    cursor.execute("SELECT stock FROM products WHERE id = ?", (laptop["id"],))
    assert cursor.fetchone()["stock"] == laptop_initial_stock - 1

    cursor.execute("SELECT stock FROM products WHERE id = ?", (mouse["id"],))
    assert cursor.fetchone()["stock"] == mouse_initial_stock - 2

    # Uso do cupom persistido em user_coupon_usages
    cursor.execute(
        "SELECT * FROM user_coupon_usages WHERE user_id = ?",
        (user_id,),
    )
    usage = cursor.fetchone()
    assert usage is not None
    assert usage["user_id"] == user_id

    # Carrinho persistido como ORDER_CREATED
    cursor.execute("SELECT status FROM carts WHERE user_id = ?", (user_id,))
    assert cursor.fetchone()["status"] == "ORDER_CREATED"
    conn.close()

    # 8. Validação de irreversibilidade (RN-009): mutações em carrinho ORDER_CREATED retornam 409
    res = requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(laptop["id"]), "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 409

    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "SALE10"},
        headers=headers,
    )
    assert res.status_code == 409


def test_e2e_api_stock_conflict_and_atomic_rollback():
    """
    Fluxo 3 (API E2E - RN-006 e RN-007):
    - user-e2e-a monta carrinho com 2 unidades de Laptop Moderno.
    - Aplica cupom SALE10 e avança para IN_CHECKOUT.
    - Simula conflito de estoque: o estoque disponível no banco cai para 1 unidade.
    - Tentativa de confirmar pedido falha com HTTP 422.
    - Validação de integridade atômica:
      * Nenhum produto tem estoque decrementado indevidamente.
      * Nenhum registro de cupom é gravado.
      * O status do carrinho permanece IN_CHECKOUT.
    - Recuperação: usuário retorna para edição (DELETE /checkout), ajusta quantidade para 1,
      inicia checkout e confirma pedido com sucesso.
    """
    user_id = "user-e2e-a"
    headers = {"X-User-ID": user_id}

    res = requests.get(f"{BASE_URL}/products")
    products = {p["name"]: p for p in res.json()}
    laptop = products["Laptop Moderno"]

    # 1. Adicionar 2 Laptops
    requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(laptop["id"]), "quantity": 2},
        headers=headers,
    )
    # Aplicar cupom
    requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "SALE10"},
        headers=headers,
    )
    # Entrar em checkout
    res = requests.post(f"{BASE_URL}/cart/checkout", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "IN_CHECKOUT"

    # 2. Simulação externa de redução de estoque concorrente para 1 unidade
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock = 1 WHERE id = ?", (laptop["id"],))
    conn.commit()
    conn.close()

    # 3. Tentar confirmar o pedido com estoque insuficiente
    res = requests.post(f"{BASE_URL}/cart/confirm", headers=headers)
    assert res.status_code == 422
    assert "Insufficient stock" in res.json()["detail"]

    # 4. Validação de Rollback Atômico no banco de dados
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT stock FROM products WHERE id = ?", (laptop["id"],))
    assert cursor.fetchone()["stock"] == 1  # Estoque não foi alterado nem negativado

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM user_coupon_usages WHERE user_id = ?",
        (user_id,),
    )
    assert cursor.fetchone()["cnt"] == 0  # Cupom não foi consumido

    cursor.execute("SELECT status FROM carts WHERE user_id = ?", (user_id,))
    assert cursor.fetchone()["status"] == "IN_CHECKOUT"  # Permanece em checkout
    conn.close()

    # 5. Fluxo de Recuperação: voltar para edição
    res = requests.delete(f"{BASE_URL}/cart/checkout", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "WITH_ITEMS"

    # Ajustar quantidade para 1
    res = requests.put(
        f"{BASE_URL}/cart/items/{laptop['id']}",
        json={"quantity": 1},
        headers=headers,
    )
    assert res.status_code == 200

    # Iniciar checkout novamente e confirmar
    requests.post(f"{BASE_URL}/cart/checkout", headers=headers)
    res = requests.post(f"{BASE_URL}/cart/confirm", headers=headers)
    assert res.status_code == 200
    assert res.json()["cart_status"] == "ORDER_CREATED"

    # Verificar estado pós-recuperação
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = ?", (laptop["id"],))
    assert cursor.fetchone()["stock"] == 0  # Decrementou de 1 para 0

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM user_coupon_usages WHERE user_id = ?",
        (user_id,),
    )
    assert cursor.fetchone()["cnt"] == 1
    conn.close()


def test_e2e_api_coupon_validation_and_single_use():
    """
    Fluxo 4 (API E2E - RN-001, RN-002, RN-003, RN-005):
    - Rejeição de cupom inexistente (HTTP 422).
    - Rejeição de cupom expirado (HTTP 422).
    - Normalização de cupom em caixa baixa com espaços (RN-003).
    - Substituição de cupom percentual por fixo (RN-001).
    - Conclusão do pedido e consumo do cupom.
    - Tentativa de reutilização do cupom pelo mesmo usuário em novo pedido é bloqueada (RN-002).
    """
    user_id = "user-e2e-a"
    headers = {"X-User-ID": user_id}

    res = requests.get(f"{BASE_URL}/products")
    laptop = next(p for p in res.json() if p["name"] == "Laptop Moderno")
    mouse = next(p for p in res.json() if p["name"] == "Mouse Sem Fio Ergonômico")

    # Adicionar 1 Laptop
    requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(laptop["id"]), "quantity": 1},
        headers=headers,
    )

    # 1. Cupom inexistente
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "NAO_EXISTE_123"},
        headers=headers,
    )
    assert res.status_code == 422
    assert "does not exist" in res.json()["detail"].lower()

    # 2. Cupom expirado
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "EXPIRADO"},
        headers=headers,
    )
    assert res.status_code == 422
    assert "expired" in res.json()["detail"].lower()

    # 3. Cupom normalizado (minúsculas com espaços)
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "  50fixo  "},
        headers=headers,
    )
    assert res.status_code == 200
    cart_data = res.json()
    assert float(cart_data["discount"]) == 50.00
    assert float(cart_data["total"]) == 4450.00

    # 4. Substituição por outro cupom válido (SALE10)
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "SALE10"},
        headers=headers,
    )
    assert res.status_code == 200
    cart_data = res.json()
    assert float(cart_data["discount"]) == 450.00  # 10% de 4500
    assert float(cart_data["total"]) == 4050.00

    # Substitui de volta para 50FIXO para validar uso único após pedido
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "50FIXO"},
        headers=headers,
    )
    assert res.status_code == 200

    # 5. Concluir compra com 50FIXO
    requests.post(f"{BASE_URL}/cart/checkout", headers=headers)
    res = requests.post(f"{BASE_URL}/cart/confirm", headers=headers)
    assert res.status_code == 200
    assert res.json()["cart_status"] == "ORDER_CREATED"

    # 6. Iniciar nova compra para o mesmo usuário
    requests.post(f"{BASE_URL}/cart", headers=headers)
    res = requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(mouse["id"]), "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 200

    # 7. Tentar aplicar 50FIXO novamente no segundo carrinho -> deve falhar (RN-002)
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "50FIXO"},
        headers=headers,
    )
    assert res.status_code == 422
    assert "already been used" in res.json()["detail"].lower()


def test_e2e_api_multi_user_isolation():
    """
    Fluxo 6 (API E2E):
    - Dois usuários (user-e2e-a e user-e2e-b) interagem simultaneamente.
    - O estado dos carrinhos é rigorosamente isolado.
    - Finalização de compra de um usuário não afeta o carrinho do outro.
    """
    user_a = "user-e2e-a"
    user_b = "user-e2e-b"
    headers_a = {"X-User-ID": user_a}
    headers_b = {"X-User-ID": user_b}

    res = requests.get(f"{BASE_URL}/products")
    products = {p["name"]: p for p in res.json()}
    laptop = products["Laptop Moderno"]
    mouse = products["Mouse Sem Fio Ergonômico"]

    # User A adiciona Laptop
    requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(laptop["id"]), "quantity": 1},
        headers=headers_a,
    )

    # User B adiciona Mouse
    requests.post(
        f"{BASE_URL}/cart/items",
        json={"product_id": str(mouse["id"]), "quantity": 1},
        headers=headers_b,
    )

    # Validação de isolamento no GET
    cart_a = requests.get(f"{BASE_URL}/cart", headers=headers_a).json()
    cart_b = requests.get(f"{BASE_URL}/cart", headers=headers_b).json()

    assert len(cart_a["items"]) == 1
    assert cart_a["items"][0]["product_id"] == str(laptop["id"])
    assert float(cart_a["total"]) == 4500.00

    assert len(cart_b["items"]) == 1
    assert cart_b["items"][0]["product_id"] == str(mouse["id"])
    assert float(cart_b["total"]) == 150.00

    # User A finaliza a compra
    requests.post(f"{BASE_URL}/cart/checkout", headers=headers_a)
    requests.post(f"{BASE_URL}/cart/confirm", headers=headers_a)

    # User B continua com carrinho intacto em WITH_ITEMS
    cart_b_after = requests.get(f"{BASE_URL}/cart", headers=headers_b).json()
    assert cart_b_after["status"] == "WITH_ITEMS"
    assert len(cart_b_after["items"]) == 1
    assert cart_b_after["items"][0]["product_id"] == str(mouse["id"])


def test_e2e_api_empty_cart_guards():
    """
    Fluxo 6 (API E2E - Guards da Máquina de Estados):
    - Tentar iniciar checkout em carrinho vazio -> HTTP 422.
    - Tentar aplicar cupom em carrinho vazio -> HTTP 422.
    - Tentar confirmar pedido fora do estado IN_CHECKOUT -> HTTP 409.
    """
    user_id = "user-e2e-a"
    headers = {"X-User-ID": user_id}

    # Carrinho vazio: checkout bloqueado
    res = requests.post(f"{BASE_URL}/cart/checkout", headers=headers)
    assert res.status_code == 422
    assert "empty cart" in res.json()["detail"].lower()

    # Carrinho vazio: aplicação de cupom bloqueada
    res = requests.post(
        f"{BASE_URL}/cart/coupon",
        json={"coupon_code": "SALE10"},
        headers=headers,
    )
    assert res.status_code == 422
    assert "empty cart" in res.json()["detail"].lower()

    # Confirmação fora de checkout bloqueada
    res = requests.post(f"{BASE_URL}/cart/confirm", headers=headers)
    assert res.status_code == 409
