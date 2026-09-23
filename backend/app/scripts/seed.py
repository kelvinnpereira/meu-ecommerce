from datetime import datetime, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models.coupon import Coupon, CouponDiscountType
from app.models.product import Product


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_data(db=None):
    close_on_exit = False
    if db is None:
        db = SessionLocal()
        close_on_exit = True

    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Seed Products
        if db.query(Product).count() == 0:
            print("Seeding products...")
            products = [
                Product(
                    name="Laptop Moderno",
                    description="Processador i7, 16GB RAM, SSD 512GB",
                    price=4500.00,
                    stock=15,
                ),
                Product(
                    name="Mouse Sem Fio Ergonômico",
                    description="Conexão Bluetooth e 2.4GHz",
                    price=150.75,
                    stock=50,
                ),
                Product(
                    name="Teclado Mecânico RGB",
                    description="Switches Blue, layout ABNT2",
                    price=350.00,
                    stock=30,
                ),
            ]
            db.add_all(products)
            db.commit()
            print("Products seeded successfully!")
        else:
            print("Products table already contains data. Skipping seed.")

        # Seed Coupons
        if db.query(Coupon).count() == 0:
            print("Seeding coupons...")
            coupons = [
                Coupon(
                    code="10OFF",
                    discount_type=CouponDiscountType.PERCENTAGE,
                    value=10.0,  # 10%
                    expires_at=utc_now() + timedelta(days=30),
                ),
                Coupon(
                    code="50FIXO",
                    discount_type=CouponDiscountType.FIXED_VALUE,
                    value=50.0,  # R$50,00
                    expires_at=utc_now() + timedelta(days=60),
                ),
                Coupon(
                    code="EXPIRADO",
                    discount_type=CouponDiscountType.PERCENTAGE,
                    value=20.0,
                    expires_at=utc_now() - timedelta(days=1),
                ),
            ]
            db.add_all(coupons)
            db.commit()
            print("Coupons seeded successfully!")
        else:
            print("Coupons table already contains data. Skipping seed.")
    finally:
        if close_on_exit:
            db.close()


if __name__ == "__main__":
    seed_data()
