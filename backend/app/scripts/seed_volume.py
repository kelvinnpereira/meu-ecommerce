"""
Volumetric synthetic data generator for e-commerce benchmark and load testing.
Uses Faker (pt_BR) with realistic domain catalogs, constraints, and relationships.
"""

import argparse
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from faker import Faker
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.cart import Cart, CartItem, CartStatusEnum
from app.models.coupon import Coupon, CouponDiscountType, UserCouponUsage
from app.models.product import Product

fake = Faker("pt_BR")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Base entities required for existing E2E/Playwright automated tests
BASE_PRODUCTS = [
    {
        "name": "Laptop Moderno",
        "description": "Processador i7, 16GB RAM, SSD 512GB",
        "price": 4500.00,
        "stock": 15,
    },
    {
        "name": "Mouse Sem Fio Ergonômico",
        "description": "Conexão Bluetooth e 2.4GHz",
        "price": 150.00,
        "stock": 50,
    },
    {
        "name": "Teclado Mecânico RGB",
        "description": "Switches Blue, layout ABNT2",
        "price": 350.00,
        "stock": 30,
    },
]

BASE_COUPONS = [
    {
        "code": "10OFF",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": Decimal("10.00"),
        "expires_in_days": 30,
        "max_uses": 1,
    },
    {
        "code": "SALE10",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": Decimal("10.00"),
        "expires_in_days": 30,
        "max_uses": 1,
    },
    {
        "code": "50FIXO",
        "discount_type": CouponDiscountType.FIXED_VALUE,
        "value": Decimal("50.00"),
        "expires_in_days": 60,
        "max_uses": 1,
    },
    {
        "code": "EXPIRADO",
        "discount_type": CouponDiscountType.PERCENTAGE,
        "value": Decimal("20.00"),
        "expires_in_days": -1,
        "max_uses": 1,
    },
]

# Realistic product catalog generators
PRODUCT_CATEGORIES = [
    {
        "category": "Informática & Notebooks",
        "items": [
            (
                "Notebook Gamer",
                [
                    "15.6'' i7 16GB RTX 3060",
                    "16'' Ryzen 7 32GB RTX 4060",
                    "17'' i9 32GB RTX 4080",
                ],
            ),
            (
                "Ultrabook Corporativo",
                [
                    "14'' i5 16GB SSD 512GB",
                    "13.3'' M2 16GB 512GB",
                    "14'' Ryzen 5 16GB SSD 256GB",
                ],
            ),
            (
                "Mini PC Desktop",
                [
                    "Ryzen 7 16GB 512GB WiFi 6",
                    "i5 16GB 1TB SSD VESA",
                    "Celeron 8GB 128GB Fanless",
                ],
            ),
            (
                "Workstation",
                [
                    "Xeon 64GB ECC RTX A2000",
                    "Threadripper 128GB RTX 4090",
                    "Core i9 64GB DDR5",
                ],
            ),
        ],
        "brands": ["Dell", "Lenovo", "Asus", "Acer", "HP", "Apple", "Avell"],
        "price_range": (2499.00, 14999.00),
    },
    {
        "category": "Monitores & Vídeo",
        "items": [
            (
                "Monitor Gamer Curvo",
                [
                    "27'' QHD 165Hz 1ms VA",
                    "32'' 4K UHD 144Hz HDR",
                    "24'' FHD 144Hz 1ms IPS",
                ],
            ),
            (
                "Monitor Ultrawide",
                [
                    "29'' FHD 75Hz IPS sRGB 99%",
                    "34'' WQHD 144Hz USB-C",
                    "49'' Super Ultrawide DQHD 240Hz",
                ],
            ),
            (
                "Monitor Profissional",
                [
                    "27'' 4K Calibrado de Fábrica",
                    "32'' 4K HDR1000 AdobeRGB",
                    "24'' Full HD Pivotante",
                ],
            ),
        ],
        "brands": ["LG", "Samsung", "Dell", "AOC", "BenQ", "Philips", "Asus ROG"],
        "price_range": (699.00, 7500.00),
    },
    {
        "category": "Periféricos & Entradas",
        "items": [
            (
                "Mouse Gamer Sem Fio",
                [
                    "26000 DPI Sensor Óptico 54g",
                    "16000 DPI RGB Recarregável",
                    "Bateria 80h PTFE Puro",
                ],
            ),
            (
                "Teclado Mecânico RGB",
                [
                    "Switch Red Hot-Swap ABNT2",
                    "Switch Brown Sem Fio 75%",
                    "Switch Blue Magnético Rapid Trigger",
                ],
            ),
            (
                "Mousepad Gamer Speed",
                [
                    "Extra Grande 900x400mm Bordas Costuradas",
                    "RGB Control 800x300mm",
                    "Tecido Cordura Resistente à Água",
                ],
            ),
            (
                "Webcam Full HD / 4K",
                [
                    "1080p 60fps com Autofoco e Ring Light",
                    "4K HDR com Microfone Duplo",
                    "1080p com Tampa de Privacidade",
                ],
            ),
            (
                "Microfone Condensador",
                [
                    "USB Cardioide com Shockmount",
                    "RGB com Pop Filter e Mute Touch",
                    "Studio XLR/USB com Braço Articulado",
                ],
            ),
        ],
        "brands": [
            "Logitech G",
            "Razer",
            "HyperX",
            "Corsair",
            "Redragon",
            "SteelSeries",
            "Fifine",
        ],
        "price_range": (39.90, 1899.00),
    },
    {
        "category": "Áudio & Som",
        "items": [
            (
                "Headset Gamer",
                [
                    "7.1 Surround Som Espacial Almofadas Memory Foam",
                    "Sem Fio 2.4GHz e Bluetooth Drivers 50mm",
                    "Com Cancelamento Ativo de Ruído",
                ],
            ),
            (
                "Fone de Ouvido Bluetooth TWS",
                [
                    "Cancelamento de Ruído ANC Modo Transparência",
                    "À Prova de Suor IPX5 Bateria 32h",
                    "Drivers Duplos Graves Profundos",
                ],
            ),
            (
                "Caixa de Som Portátil Bluetooth",
                [
                    "20W RMS IPX7 Bateria 12 Horas",
                    "60W RMS com Iluminação LED",
                    "10W RMS Ultra Compacta",
                ],
            ),
            (
                "Soundbar para PC e TV",
                [
                    "2.1 Canais 160W com Subwoofer Sem Fio",
                    "Bluetooth 5.0 com Entrada Óptica e HDMI",
                    "Compacta USB 30W",
                ],
            ),
        ],
        "brands": [
            "JBL",
            "Sony",
            "Edifier",
            "Anker Soundcore",
            "Audio-Technica",
            "Sennheiser",
        ],
        "price_range": (79.00, 2490.00),
    },
    {
        "category": "Armazenamento & Memória",
        "items": [
            (
                "SSD NVMe M.2 PCIe 4.0",
                [
                    "1TB Leitura 7400MB/s Gravação 6500MB/s",
                    "2TB Leitura 7000MB/s com Dissipador",
                    "500GB Leitura 3500MB/s",
                ],
            ),
            (
                "SSD SATA III 2.5''",
                [
                    "480GB Leitura 540MB/s",
                    "960GB Leitura 550MB/s",
                    "2TB Alta Durabilidade",
                ],
            ),
            (
                "Memória RAM Gamer",
                [
                    "16GB (2x8GB) DDR4 3200MHz CL16",
                    "32GB (2x16GB) DDR5 6000MHz RGB",
                    "16GB DDR4 2666MHz",
                ],
            ),
            (
                "HD Externo Portátil",
                [
                    "1TB USB 3.0 Antichoque",
                    "2TB Backup Plus",
                    "4TB Seguro com Criptografia",
                ],
            ),
            (
                "Cartão de Memória MicroSD",
                [
                    "128GB Extreme Pro 170MB/s A2 V30",
                    "256GB Ultra C10",
                    "64GB Endurance para Câmeras",
                ],
            ),
        ],
        "brands": [
            "Kingston",
            "Samsung EVO",
            "Crucial",
            "SanDisk",
            "Corsair Vengeance",
            "WD Black",
        ],
        "price_range": (45.00, 1850.00),
    },
    {
        "category": "Casa Inteligente & Redes",
        "items": [
            (
                "Roteador Wi-Fi 6 Mesh",
                [
                    "Dual Band AX3000 Gigabit 4 Antenas",
                    "Tri-Band AX6000 Pack com 2 Unidades",
                    "AX1800 Fácil Configuração",
                ],
            ),
            (
                "Lâmpada Inteligente Wi-Fi",
                [
                    "10W RGB 16 Milhões de Cores Alexa/Google",
                    "Filamento Vintage Dimerizável",
                    "Spot GU10 Inteligente",
                ],
            ),
            (
                "Tomada Inteligente Wi-Fi",
                [
                    "16A com Monitoramento de Consumo de Energia",
                    "10A Bivolt Temporizador",
                    "Filtro de Linha Wi-Fi 4 Tomadas",
                ],
            ),
            (
                "Câmera de Segurança Inteligente",
                [
                    "Wi-Fi 360° Full HD Visão Noturna Áudio Bidirecional",
                    "Externa IP66 com Holofote e Sirene",
                    "Interna com Detecção Humana IA",
                ],
            ),
            (
                "Switch de Rede Gigabit",
                [
                    "8 Portas 10/100/1000 Mbps Não Gerenciável",
                    "5 Portas Metálico Silencioso",
                    "16 Portas Rack",
                ],
            ),
        ],
        "brands": [
            "TP-Link",
            "Intelbras",
            "D-Link",
            "Xiaomi",
            "Geonav",
            "Positivo Casa Inteligente",
        ],
        "price_range": (35.00, 1290.00),
    },
    {
        "category": "Acessórios & Cabos",
        "items": [
            (
                "Cabo HDMI 2.1 Ultra High Speed",
                [
                    "8K 60Hz / 4K 120Hz 2m Blindado em Nylon",
                    "3m Conectores Banhados a Ouro",
                    "1.5m Certificado",
                ],
            ),
            (
                "Hub Adaptador USB-C",
                [
                    "7 em 1 HDMI 4K USB 3.0 Cartões SD PD 100W",
                    "5 em 1 Alumínio Espacial",
                    "10 em 1 com RJ45 Gigabit e Dual HDMI",
                ],
            ),
            (
                "Carregador de Parede GaN",
                [
                    "65W Rápido 3 Portas USB-C/USB-A",
                    "30W Compacto para Smartphone",
                    "100W 4 Portas para Notebook",
                ],
            ),
            (
                "Cabo USB-C para USB-C / Lightning",
                [
                    "100W 2m Trançado com Display de Potência",
                    "MFi 20W 1.2m Reforçado",
                    "Silicone Macio 60W",
                ],
            ),
            (
                "Suporte para Notebook / Tablet",
                [
                    "Alumínio Articulado Ergonômico Dobrável",
                    "Com Cooler Duplo RGB",
                    "Vertical Regulável",
                ],
            ),
        ],
        "brands": ["UGreen", "Baseus", "Anker", "I2GO", "Geonav", "Elg"],
        "price_range": (14.90, 480.00),
    },
    {
        "category": "Mobiliário & Escritório",
        "items": [
            (
                "Cadeira Ergonômica de Escritório",
                [
                    "Presidente Tela Mesh Ajuste Lombar 3D Braços 4D",
                    "Diretor com Encosto Reclinável e Apoio de Cabeça",
                    "Executiva com Pistão a Gás Classe 4",
                ],
            ),
            (
                "Suporte Articulado a Gás para Monitor",
                [
                    "Pistão a Gás para Monitores 17'' a 35'' com Passa-cabos",
                    "Duplo para 2 Monitores até 32''",
                    "De Mesa com Fixação Morsa",
                ],
            ),
            (
                "Mesa com Regulagem Elétrica de Altura",
                [
                    "Tampo 140x70cm 2 Motores Silenciosos 4 Memórias",
                    "Estrutura Stand-up Desk com Display Digital",
                ],
            ),
            (
                "Apoio Ergonômico de Pés",
                [
                    "Com Regulagem de Altura e Inclinação Rolos de Massagem",
                    "Anti-fadiga em Espuma de Alta Densidade",
                ],
            ),
            (
                "Luminária Articulada de Mesa",
                [
                    "LED Touch com 5 Modos de Cor e Dimmer Timer",
                    "Barra de Luz Screenbar para Monitor USB",
                ],
            ),
        ],
        "brands": ["Flexform", "Elements", "Comfy", "Elg", "DT3", "Husky"],
        "price_range": (89.90, 3999.00),
    },
]


def generate_unique_product_records(
    target_count: int, existing_names: Set[str]
) -> List[Dict]:
    """Generates realistic e-commerce product records with varied stock and prices."""
    records = []
    generated_names = set(existing_names)

    for cat_data in PRODUCT_CATEGORIES:
        brand_list = cat_data["brands"]
        items_list = cat_data["items"]
        min_p, max_p = cat_data["price_range"]

        for prod_base, specs_list in items_list:
            for spec in specs_list:
                for brand in brand_list:
                    if len(records) >= target_count:
                        break

                    # Construct realistic title
                    candidate_name = f"{prod_base} {brand} {spec}".strip()
                    if len(candidate_name) > 100:
                        candidate_name = candidate_name[:97] + "..."

                    if candidate_name in generated_names:
                        # Append a model variant code
                        variant_code = fake.bothify("Mod. ##??").upper()
                        candidate_name = f"{candidate_name[:85]} {variant_code}".strip()

                    if candidate_name in generated_names:
                        continue

                    generated_names.add(candidate_name)

                    # Stock distributions:
                    # 5% out of stock, 15% low stock (1-3), 70% regular (10-150), 10% high volume (200-800)
                    stock_dice = random.random()
                    if stock_dice < 0.05:
                        stock = 0
                    elif stock_dice < 0.20:
                        stock = random.randint(1, 3)
                    elif stock_dice < 0.90:
                        stock = random.randint(10, 150)
                    else:
                        stock = random.randint(200, 800)

                    # Price with natural variation
                    base_price = random.uniform(min_p, max_p)
                    # Round to realistic psychological cents (.90, .99, .00, .50)
                    cents_choice = random.choice([0.90, 0.99, 0.00, 0.50, 0.49, 0.79])
                    price = round(int(base_price) + cents_choice, 2)
                    if price <= 0:
                        price = 9.99

                    # 85% with detailed specs description, 15% None
                    if random.random() < 0.85:
                        desc_phrases = [
                            f"Produto original {brand} com garantia de 12 meses.",
                            "Ideal para alta performance e produtividade no dia a dia.",
                            f"Especificações principais: {spec}.",
                            "Excelente acabamento e durabilidade comprovada no segmento.",
                        ]
                        desc = f"{' '.join(desc_phrases[: random.randint(2, 3)])}"
                        if len(desc) > 255:
                            desc = desc[:252] + "..."
                    else:
                        desc = None

                    records.append(
                        {
                            "name": candidate_name,
                            "description": desc,
                            "price": price,
                            "stock": stock,
                        }
                    )

                if len(records) >= target_count:
                    break
            if len(records) >= target_count:
                break
        if len(records) >= target_count:
            break

    # If still need more to fulfill target_count, generate procedural branded tech items
    while len(records) < target_count:
        cat_data = random.choice(PRODUCT_CATEGORIES)
        brand = random.choice(cat_data["brands"])
        prod_base = random.choice(cat_data["items"])[0]
        suffix = fake.bothify("V## Pro Edition-?").upper()
        name = f"{prod_base} {brand} {suffix}"[:100]
        if name in generated_names:
            continue
        generated_names.add(name)

        min_p, max_p = cat_data["price_range"]
        price = round(random.uniform(min_p, max_p), 2)
        stock = random.choice([0, 1, 5, 25, 50, 120, 300])
        desc = (
            f"Equipamento {brand} de ponta com tecnologia avançada. Lançamento."
            if random.random() < 0.85
            else None
        )

        records.append(
            {
                "name": name,
                "description": desc,
                "price": price,
                "stock": stock,
            }
        )

    return records


def generate_unique_coupons(target_count: int, existing_codes: Set[str]) -> List[Dict]:
    """Generates realistic promotional coupons with % and fixed discounts, active and expired."""
    coupons = []
    generated_codes = {code.upper() for code in existing_codes}

    prefixes = [
        "PROMO",
        "TECH",
        "DESCONTO",
        "BEMVINDO",
        "CLIENTE",
        "VIP",
        "FRETE",
        "BLACK",
        "CYBER",
        "SUPER",
        "APP",
        "VERAO",
        "INVERNO",
        "PRIME",
        "FESTA",
        "GAMER",
        "OFF",
        "SPECIAL",
        "FLASH",
        "MEGA",
        "ECONOMIA",
        "TURBO",
    ]

    now = utc_now()

    while len(coupons) < target_count:
        prefix = random.choice(prefixes)
        discount_dice = random.random()

        if discount_dice < 0.60:
            # PERCENTAGE (5% to 70%)
            disc_type = CouponDiscountType.PERCENTAGE
            pct_val = random.choice(
                [5.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0]
            )
            val = Decimal(str(pct_val))
            code = f"{prefix}{int(pct_val)}"
        else:
            # FIXED_VALUE (R$ 10.00 to R$ 500.00)
            disc_type = CouponDiscountType.FIXED_VALUE
            fix_val = random.choice(
                [
                    10.0,
                    15.0,
                    20.0,
                    25.0,
                    30.0,
                    50.0,
                    75.0,
                    100.0,
                    150.0,
                    200.0,
                    300.0,
                    500.0,
                ]
            )
            val = Decimal(str(fix_val))
            code = f"{prefix}FIXO{int(fix_val)}"

        # Make sure code is unique
        if code in generated_codes:
            suffix = fake.bothify("##?").upper()
            code = f"{code}_{suffix}"

        if code in generated_codes:
            continue

        generated_codes.add(code)

        # Expiry date variations:
        # 70% active future (+1 to +180 days)
        # 25% expired (-1 to -365 days)
        # 5% borderline expiring today (+2 to +12 hours)
        exp_dice = random.random()
        if exp_dice < 0.70:
            expires_at = now + timedelta(
                days=random.randint(1, 180), minutes=random.randint(0, 1440)
            )
        elif exp_dice < 0.95:
            expires_at = now - timedelta(
                days=random.randint(1, 365), minutes=random.randint(0, 1440)
            )
        else:
            expires_at = now + timedelta(hours=random.randint(2, 12))

        max_uses = random.choices([1, 2, 3, 5], weights=[70, 15, 10, 5])[0]

        coupons.append(
            {
                "code": code,
                "discount_type": disc_type,
                "value": val,
                "expires_at": expires_at,
                "max_uses_per_user": max_uses,
            }
        )

    return coupons


def seed_volumetric_data(
    db: Optional[Session] = None,
    clean: bool = False,
    products_target: int = 500,
    coupons_target: int = 150,
    carts_target: int = 1000,
) -> Dict[str, int]:
    """
    Executes relational volumetric synthetic seed insertion.
    Returns a dictionary with record count generated/present per entity.
    """
    close_session_on_exit = False
    if db is None:
        db = SessionLocal()
        close_session_on_exit = True

    try:
        # Ensure schema tables exist
        Base.metadata.create_all(bind=engine)

        if clean:
            print("[Clean Mode] Removing existing data in relational order...")
            db.query(UserCouponUsage).delete()
            db.query(CartItem).delete()
            db.query(Cart).delete()
            db.query(Coupon).delete()
            db.query(Product).delete()
            db.commit()
            print("[Clean Mode] All tables cleared successfully.")

        # ==========================================
        # 1. SEED PRODUCTS
        # ==========================================
        existing_products = db.query(Product).all()
        existing_prod_names = {p.name for p in existing_products}

        # Ensure base products exist (for test suites)
        for base_p in BASE_PRODUCTS:
            if base_p["name"] not in existing_prod_names:
                new_prod = Product(**base_p)
                db.add(new_prod)
                existing_prod_names.add(base_p["name"])
        db.commit()

        current_prod_count = db.query(Product).count()
        needed_prods = max(0, products_target - current_prod_count)

        if needed_prods > 0:
            print(
                f"Generating {needed_prods} realistic product records (target: {products_target})..."
            )
            new_prod_dicts = generate_unique_product_records(
                needed_prods, existing_prod_names
            )
            product_objects = [Product(**p_data) for p_data in new_prod_dicts]
            db.bulk_save_objects(product_objects)
            db.commit()

        all_products = db.query(Product).all()
        prod_count = len(all_products)
        print(f"✓ Products table: {prod_count} records.")

        # ==========================================
        # 2. SEED COUPONS
        # ==========================================
        existing_coupons = db.query(Coupon).all()
        existing_coupon_codes = {c.code.upper() for c in existing_coupons}

        # Ensure base coupons exist
        now = utc_now()
        for base_c in BASE_COUPONS:
            if base_c["code"].upper() not in existing_coupon_codes:
                expires_at = now + timedelta(days=base_c["expires_in_days"])
                new_coupon = Coupon(
                    code=base_c["code"],
                    discount_type=base_c["discount_type"],
                    value=base_c["value"],
                    expires_at=expires_at,
                    max_uses_per_user=base_c["max_uses"],
                )
                db.add(new_coupon)
                existing_coupon_codes.add(base_c["code"].upper())
        db.commit()

        current_coupon_count = db.query(Coupon).count()
        needed_coupons = max(0, coupons_target - current_coupon_count)

        if needed_coupons > 0:
            print(
                f"Generating {needed_coupons} realistic coupon records (target: {coupons_target})..."
            )
            new_coupon_dicts = generate_unique_coupons(
                needed_coupons, existing_coupon_codes
            )
            coupon_objects = [Coupon(**c_data) for c_data in new_coupon_dicts]
            db.bulk_save_objects(coupon_objects)
            db.commit()

        all_coupons = db.query(Coupon).all()
        coupon_count = len(all_coupons)
        print(f"✓ Coupons table: {coupon_count} records.")

        # Segregate active coupons for cart usage
        active_coupons = [c for c in all_coupons if c.expires_at > now]
        if not active_coupons:
            active_coupons = all_coupons

        # ==========================================
        # 3. SEED CARTS, CART ITEMS & USAGES
        # ==========================================
        current_cart_count = db.query(Cart).count()
        needed_carts = max(0, carts_target - current_cart_count)

        if needed_carts > 0:
            print(
                f"Generating {needed_carts} carts with distributed lifecycles (target: {carts_target})..."
            )

            # Cart status distribution for needed_carts:
            # 15% EMPTY, 35% WITH_ITEMS, 15% IN_CHECKOUT, 25% ORDER_CREATED, 10% ABANDONED
            status_dist = (
                [CartStatusEnum.EMPTY] * int(needed_carts * 0.15)
                + [CartStatusEnum.WITH_ITEMS] * int(needed_carts * 0.35)
                + [CartStatusEnum.IN_CHECKOUT] * int(needed_carts * 0.15)
                + [CartStatusEnum.ORDER_CREATED] * int(needed_carts * 0.25)
            )
            # Fill remaining to match exact needed_carts with ABANDONED
            remaining = needed_carts - len(status_dist)
            status_dist.extend([CartStatusEnum.ABANDONED] * remaining)
            random.shuffle(status_dist)

            # Generate pool of unique users (~750 users for 1000 carts)
            unique_users_count = max(50, int(needed_carts * 0.75))
            user_pool = [
                f"usr_{fake.hexify(text='^^^^^^^^', upper=False)}"
                for _ in range(unique_users_count)
            ]

            # Track user coupon usages to respect max_uses_per_user
            user_coupon_usages_map: Dict[Tuple[str, int], int] = {}
            for usage in db.query(UserCouponUsage).all():
                user_coupon_usages_map[(usage.user_id, usage.coupon_id)] = (
                    user_coupon_usages_map.get((usage.user_id, usage.coupon_id), 0) + 1
                )

            # Insert carts in batches so we have primary keys for CartItems & Usages
            created_carts: List[Cart] = []

            for i, status in enumerate(status_dist):
                user_id = random.choice(user_pool)

                # Coupon decision based on cart status
                coupon_id = None
                if status != CartStatusEnum.EMPTY:
                    # Decide if cart has coupon
                    has_coupon_chance = {
                        CartStatusEnum.WITH_ITEMS: 0.25,
                        CartStatusEnum.IN_CHECKOUT: 0.40,
                        CartStatusEnum.ORDER_CREATED: 0.55,
                        CartStatusEnum.ABANDONED: 0.15,
                    }.get(status, 0.0)

                    if random.random() < has_coupon_chance:
                        chosen_coupon = random.choice(active_coupons)
                        # Check usage limits if ORDER_CREATED
                        current_uses = user_coupon_usages_map.get(
                            (user_id, chosen_coupon.id), 0
                        )
                        if current_uses < chosen_coupon.max_uses_per_user:
                            coupon_id = chosen_coupon.id

                # Realistic timestamps over the last 90 days
                days_ago = random.randint(0, 90)
                minutes_ago = random.randint(10, 1440)
                cart_created_at = now - timedelta(days=days_ago, minutes=minutes_ago)
                cart_updated_at = cart_created_at + timedelta(
                    minutes=random.randint(1, 120)
                )

                cart = Cart(
                    user_id=user_id,
                    status=status,
                    coupon_id=coupon_id,
                    created_at=cart_created_at,
                    updated_at=cart_updated_at,
                )
                created_carts.append(cart)

            # Save carts
            db.add_all(created_carts)
            db.commit()

            print(
                f"Created {len(created_carts)} carts. Now populating items and coupon usages..."
            )

            # ==========================================
            # 4. SEED CART ITEMS & USER COUPON USAGES
            # ==========================================
            items_to_create: List[CartItem] = []
            usages_to_create: List[UserCouponUsage] = []

            for cart in created_carts:
                if cart.status == CartStatusEnum.EMPTY:
                    continue

                # Number of items per cart: 1-2 items (60%), 3-4 items (30%), 5-8 items (10%)
                num_items = random.choices(
                    [1, 2, 3, 4, 5, 6, 7, 8], weights=[35, 25, 18, 12, 5, 3, 1, 1]
                )[0]
                selected_products = random.sample(
                    all_products, min(num_items, len(all_products))
                )

                for prod in selected_products:
                    # Quantities: mostly 1 to 4; occasionally 10-25 for bulk testing
                    if random.random() < 0.95:
                        qty = random.randint(1, 4)
                    else:
                        qty = random.randint(5, 25)

                    items_to_create.append(
                        CartItem(
                            cart_id=cart.id,
                            product_id=str(prod.id),
                            quantity=qty,
                            unit_price=Decimal(str(round(prod.price, 2))),
                        )
                    )

                # If ORDER_CREATED and coupon was applied, record usage
                if (
                    cart.status == CartStatusEnum.ORDER_CREATED
                    and cart.coupon_id is not None
                ):
                    order_id = f"ORD-2026-{cart.id:06d}"
                    usages_to_create.append(
                        UserCouponUsage(
                            user_id=cart.user_id,
                            coupon_id=cart.coupon_id,
                            order_id=order_id,
                        )
                    )
                    user_coupon_usages_map[(cart.user_id, cart.coupon_id)] = (
                        user_coupon_usages_map.get((cart.user_id, cart.coupon_id), 0)
                        + 1
                    )

            # Bulk save items in batches of 1000
            batch_size = 1000
            for i in range(0, len(items_to_create), batch_size):
                db.bulk_save_objects(items_to_create[i : i + batch_size])
            db.commit()

            # Save usages
            if usages_to_create:
                db.bulk_save_objects(usages_to_create)
                db.commit()

        final_cart_count = db.query(Cart).count()
        final_item_count = db.query(CartItem).count()
        final_usage_count = db.query(UserCouponUsage).count()

        print(f"✓ Carts table: {final_cart_count} records.")
        print(f"✓ CartItems table: {final_item_count} records.")
        print(f"✓ UserCouponUsages table: {final_usage_count} records.")

        return {
            "products": prod_count,
            "coupons": coupon_count,
            "carts": final_cart_count,
            "cart_items": final_item_count,
            "user_coupon_usages": final_usage_count,
        }

    finally:
        if close_session_on_exit:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed volumetric synthetic database.")
    parser.add_argument(
        "--clean", action="store_true", help="Clear tables before seeding."
    )
    parser.add_argument(
        "--products", type=int, default=500, help="Target product count (default: 500)."
    )
    parser.add_argument(
        "--coupons", type=int, default=150, help="Target coupon count (default: 150)."
    )
    parser.add_argument(
        "--carts", type=int, default=1000, help="Target cart count (default: 1000)."
    )

    args = parser.parse_args()

    print("==================================================")
    print("  E-COMMERCE BENCHMARK: VOLUMETRIC SEED GENERATOR")
    print("==================================================")
    results = seed_volumetric_data(
        clean=args.clean,
        products_target=args.products,
        coupons_target=args.coupons,
        carts_target=args.carts,
    )
    print("--------------------------------------------------")
    print(f"Total Products:           {results['products']}")
    print(f"Total Coupons:            {results['coupons']}")
    print(f"Total Carts:              {results['carts']}")
    print(f"Total Cart Items:         {results['cart_items']}")
    print(f"Total User Coupon Usages: {results['user_coupon_usages']}")
    total_records = sum(results.values())
    print(f"Total Database Records:   {total_records}")
    print("==================================================")


if __name__ == "__main__":
    main()
