import sqlite3

import pytest


@pytest.fixture(autouse=True)
def prepare_e2e_db():
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    # Ensure Mouse price is 150.00 for e2e tests
    cursor.execute(
        "UPDATE products SET price = 150.00 WHERE name = 'Mouse Sem Fio Ergonômico'"
    )
    # Ensure SALE10 coupon exists
    cursor.execute("SELECT id FROM coupons WHERE code = 'SALE10'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO coupons (code, discount_type, value, expires_at, max_uses_per_user) VALUES (?, ?, ?, ?, ?)",
            ("SALE10", "PERCENTAGE", 10.0, "2099-01-01 00:00:00", 100),
        )
    # Clear user-123 cart
    cursor.execute(
        "DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id = 'user-123')"
    )
    cursor.execute("DELETE FROM carts WHERE user_id = 'user-123'")
    conn.commit()
    conn.close()
    yield
    # Cleanup cart after test
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id = 'user-123')"
    )
    cursor.execute("DELETE FROM carts WHERE user_id = 'user-123'")
    conn.commit()
    conn.close()
