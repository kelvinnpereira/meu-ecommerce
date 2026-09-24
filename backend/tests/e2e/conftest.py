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
    # Ensure 50FIXO coupon exists
    cursor.execute("SELECT id FROM coupons WHERE code = '50FIXO'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO coupons (code, discount_type, value, expires_at, max_uses_per_user) VALUES (?, ?, ?, ?, ?)",
            ("50FIXO", "FIXED_VALUE", 50.0, "2099-01-01 00:00:00", 100),
        )
    # Ensure EXPIRADO coupon exists
    cursor.execute("SELECT id FROM coupons WHERE code = 'EXPIRADO'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO coupons (code, discount_type, value, expires_at, max_uses_per_user) VALUES (?, ?, ?, ?, ?)",
            ("EXPIRADO", "PERCENTAGE", 20.0, "2020-01-01 00:00:00", 100),
        )
    # Clear test users' carts and coupon usages
    test_users = ("user-123", "user-e2e-a", "user-e2e-b")
    placeholders = ",".join("?" for _ in test_users)
    cursor.execute(
        f"DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id IN ({placeholders}))",
        test_users,
    )
    cursor.execute(f"DELETE FROM carts WHERE user_id IN ({placeholders})", test_users)
    cursor.execute(
        f"DELETE FROM user_coupon_usages WHERE user_id IN ({placeholders})", test_users
    )
    # Restore product stocks
    cursor.execute("UPDATE products SET stock = 15 WHERE name = 'Laptop Moderno'")
    cursor.execute(
        "UPDATE products SET stock = 50 WHERE name = 'Mouse Sem Fio Ergonômico'"
    )
    cursor.execute("UPDATE products SET stock = 30 WHERE name = 'Teclado Mecânico RGB'")
    conn.commit()
    conn.close()
    yield
    # Cleanup cart and coupon usages after test
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id IN ({placeholders}))",
        test_users,
    )
    cursor.execute(f"DELETE FROM carts WHERE user_id IN ({placeholders})", test_users)
    cursor.execute(
        f"DELETE FROM user_coupon_usages WHERE user_id IN ({placeholders})", test_users
    )
    cursor.execute("UPDATE products SET stock = 15 WHERE name = 'Laptop Moderno'")
    cursor.execute(
        "UPDATE products SET stock = 50 WHERE name = 'Mouse Sem Fio Ergonômico'"
    )
    cursor.execute("UPDATE products SET stock = 30 WHERE name = 'Teclado Mecânico RGB'")
    conn.commit()
    conn.close()
