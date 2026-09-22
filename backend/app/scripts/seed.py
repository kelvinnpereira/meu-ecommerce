from app.database import SessionLocal, engine, Base
from app.models.product import Product


def seed_data():
    # Create tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db = SessionLocal()
    try:
        # Check if there is already data
        if db.query(Product).count() == 0:
            print("Seeding database...")
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
            print("Database seeded successfully!")
        else:
            print("Database already contains data. Skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
