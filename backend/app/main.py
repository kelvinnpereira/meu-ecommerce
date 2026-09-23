from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import cart, health, products
from app.database import Base, engine
from app.models import cart as cart_model, coupon, product  # noqa: F401

Base.metadata.create_all(bind=engine)  # Cria as tabelas

app = FastAPI(title="Meu E-commerce API")


# CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",  # For Live Server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["cart"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Meu E-commerce API"}
