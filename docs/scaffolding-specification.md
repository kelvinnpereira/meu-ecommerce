# Especificação do Scaffolding Inicial

Este documento define a arquitetura, convenções, ferramentas e a implementação de referência para o scaffolding do projeto de e-commerce. O objetivo deste scaffolding é fornecer uma base sólida e testável, incluindo um fluxo vertical completo de **Listagem de Produtos** (do banco de dados até a apresentação no frontend, com testes E2E).

---

## 1. Visão Geral e Decisões Centrais

O projeto é um e-commerce didático projetado para demonstrar boas práticas de arquitetura em camadas e integração contínua orientada a testes.

*   **Backend:** Python 3.11+ utilizando o framework **FastAPI**.
*   **Banco de Dados:** **SQLite**, persistido através de volumes Docker para unir a agilidade do desenvolvimento com a portabilidade.
*   **Camada de Acesso a Dados:** **SQLAlchemy** (2.x) implementando o padrão *Repository*.
*   **Frontend:** HTML5 e Vanilla JavaScript (sem frameworks SPA), dividido em camadas claras (*Presentation*, *Domain*, *API*), servido via contêiner Nginx ou estaticamente via backend.
*   **Infraestrutura:** Docker e Docker Compose orquestrando o ambiente completo.
*   **Testes:** Suíte unificada com **pytest** e **Playwright** (Python), cobrindo testes unitários, testes de integração de API e testes E2E de navegador.
*   **Ferramentas:** `Makefile` para padronização e automação de comandos do ciclo de vida.

---

## 2. Estrutura de Diretórios

```
meu-ecommerce/
├── .gitignore
├── .dockerignore
├── Makefile                       # Ponto de entrada de comandos de automação
├── docker-compose.yml             # Orquestrador de serviços (backend, frontend)
├── docs/                          # Documentação e especificações
│   ├── scaffolding-specification.md
│   └── ...
├── frontend/                      # Camada de apresentação (despretensiosa, modular)
│   ├── index.html                 # Página de visualização de produtos
│   ├── css/
│   │   └── style.css              # Estilos mínimos para layout
│   └── js/
│       ├── api/
│       │   └── productsApi.js     # Comunicação HTTP (fetch) com o backend
│       ├── domain/
│       │   └── product.js         # Validações e formatações de produto no frontend
│       └── views/
│           └── productView.js     # Manipulação de DOM para renderizar o catálogo
└── backend/                       # Aplicação FastAPI em camadas
    ├── Dockerfile                 # Configuração do contêiner do backend + Playwright
    ├── requirements.txt           # Dependências de produção
    ├── requirements-dev.txt       # Dependências de testes e ferramentas de qualidade
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                # Instância FastAPI, middlewares e registro de rotas
    │   ├── database.py            # Engine do SQLAlchemy e SessionLocal
    │   ├── models/                # Modelos ORM (tabelas do banco)
    │   │   ├── __init__.py
    │   │   └── product.py
    │   ├── schemas/               # Schemas Pydantic (validação de entrada/saída de dados)
    │   │   ├── __init__.py
    │   │   └── product.py
    │   ├── repositories/          # Camada de Acesso a Dados (SQLAlchemy)
    │   │   ├── __init__.py
    │   │   └── product_repository.py
    │   ├── services/              # Camada de Regra de Negócio
    │   │   ├── __init__.py
    │   │   └── product_service.py
    │   └── api/                   # Camada de Controllers / Routers
    │       ├── __init__.py
    │       ├── deps.py            # Injeção de dependência (sessão do DB, etc.)
    │       └── v1/
    │           ├── __init__.py
    │           └── endpoints/
    │               ├── __init__.py
    │               ├── health.py  # Endpoint /health
    │               └── products.py# Endpoint /api/v1/products
    └── tests/                     # Suíte de testes integrada
        ├── conftest.py            # Fixtures (TestClient, DB SQLite em memória/teste)
        ├── unit/                  # Testes unitários (Services, Schemas)
        │   └── test_product_service.py
        ├── integration/           # Testes de integração de endpoints (API)
        │   └── test_products_endpoint.py
        └── e2e/                   # Testes de fluxo ponta a ponta (Playwright)
            └── test_product_listing_ui.py
```

---

## 3. Stack e Dependências

### 3.1 Backend (`requirements.txt`)

*   `fastapi>=0.110.0`: Framework web de alta performance.
*   `uvicorn[standard]>=0.28.0`: Servidor ASGI para executar a aplicação.
*   `sqlalchemy>=2.0.0`: ORM para mapeamento objeto-relacional.
*   `pydantic>=2.0.0`: Validação de tipos e serialização de dados.

### 3.2 Desenvolvimento e Testes (`requirements-dev.txt`)

*   `pytest>=8.0.0`: Framework de execução de testes.
*   `httpx>=0.27.0`: Cliente HTTP assíncrono para o `TestClient` do FastAPI.
*   `pytest-playwright>=0.4.0`: Plugin Playwright para automação de testes no navegador.
*   `ruff>=0.3.0`: Linter e formatador de código ultrarrápido em Rust.
*   `black>=24.0.0`: Formatador de código opinativo para padronização.

---

## 4. Convenções Adotadas

*   **Padrão Arquitetural Backend:** Estritamente `Controller (Endpoint) -> Service -> Repository`.
    *   *Controller:* Valida DTOs de entrada e serializa saída. Não contém SQL nem regra de negócio.
    *   *Service:* Contém lógica de negócio pura, validações de regra e orquestra operações.
    *   *Repository:* Executa operações do SQLAlchemy sobre o banco de dados.
*   **Convenções de Nomenclatura:**
    *   Arquivos e pastas Python: `snake_case` (ex: `product_repository.py`).
    *   Classes Python: `PascalCase` (ex: `ProductRepository`).
    *   Arquivos JavaScript: `camelCase` (ex: `productsApi.js`).
    *   Endpoints de API: Plural e kebab-case (ex: `/api/v1/products`).
*   **Commits:** Padrão Conventional Commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`).

---

## 5. Especificação do Fluxo Vertical de Scaffolding (Listagem de Produtos)

Para validar a integridade do boilerplate do banco à interface, implementa-se o primeiro slice vertical.

### 5.1 Entidade Produto

*   `id`: Inteiro, Chave Primária, Auto-incremento.
*   `name`: String(100), Não nulo.
*   `description`: String(255), Opcional.
*   `price`: Float / Decimal, Não nulo.
*   `stock`: Inteiro, Não nulo, Default 0.

### 5.2 Contratos da API

*   `GET /health`:
    *   Resposta: `{"status": "ok"}`
*   `GET /api/v1/products`:
    *   Resposta (200 OK):
        ```json
        [
          {
            "id": 1,
            "name": "Produto Demonstração",
            "description": "Item de teste inicial",
            "price": 99.90,
            "stock": 10
          }
        ]
        ```

### 5.3 Camada de Apresentação (Frontend)

*   `index.html`: Contém container `<div id="products-container">` e estado de carregamento.
*   `productsApi.js`: Função assíncrona `fetchProducts()` que consome o endpoint `/api/v1/products`.
*   `productView.js`: Função `renderProducts(products)` que injeta cards de produtos com nome, preço, descrição e botão (inativo nesta fase) no DOM.

---

## 6. Estratégia de Testes

Os testes são divididos em 3 categorias e executados pelo mesmo runner (`pytest`):

1.  **Testes Unitários (`tests/unit/`):**
    *   Testam a lógica de `ProductService` utilizando repositórios mockados.
2.  **Testes de Integração de Endpoint (`tests/integration/`):**
    *   Testam a rota `GET /api/v1/products` usando `TestClient` (HTTPX) e um banco SQLite em memória, validando status code 200 e payload JSON.
3.  **Testes E2E de Frontend (`tests/e2e/`):**
    *   Utilizam o Playwright para abrir a página web no navegador Chromium, esperar o carregamento da lista de produtos e verificar se os nomes e preços esperados aparecem na tela renderizada.

---

## 7. Makefile e Automação de Comandos

O arquivo `Makefile` deve implementar os seguintes targets padronizados:

```makefile
.PHONY: up down test format logs seed

up:
	docker-compose up --build -d

down:
	docker-compose down --volumes

logs:
	docker-compose logs -f

test:
	docker-compose exec backend pytest -v

format:
	docker-compose exec backend ruff check --fix .
	docker-compose exec backend black .

seed:
	docker-compose exec backend python -m app.scripts.seed
```

---

## 8. Configuração de Contêineres e Persistência

*   O arquivo SQLite (`ecommerce.db`) é salvo no diretório `/data/ecommerce.db` dentro do contêiner do backend.
*   Um volume nomeado (`backend_data`) é mapeado para `/data`, garantindo que os dados persistam entre reinicializações dos contêineres.
*   O Dockerfile do backend inclui as dependências do sistema necessárias para a execução do Playwright em modo headless (Chromium).
