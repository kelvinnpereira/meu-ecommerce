# Meu E-commerce

Sistema de e-commerce didático projetado para demonstrar uma **arquitetura em camadas estrita**, orientada a boas práticas de engenharia de software, cobertura abrangente de testes automatizados (unitários, integração e E2E com Playwright) e endurecimento de segurança (*security hardening* contra OWASP Top 10).

---

## Sumário

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
  - [Padrão em Camadas (Backend)](#padrão-em-camadas-backend)
  - [Estrutura do Frontend](#estrutura-do-frontend)
  - [Árvore de Diretórios](#árvore-de-diretórios)
- [Funcionalidades e Regras de Negócio](#funcionalidades-e-regras-de-negócio)
  - [Catálogo de Produtos](#catálogo-de-produtos)
  - [Carrinho de Compras e Máquina de Estados](#carrinho-de-compras-e-máquina-de-estados)
  - [Sistema de Cupons de Desconto](#sistema-de-cupons-de-desconto)
  - [Checkout e Confirmação Atômica de Pedidos](#checkout-e-confirmação-atômica-de-pedidos)
  - [Hardening de Segurança (Red Team)](#hardening-de-segurança-red-team)
- [Endpoints da API REST](#endpoints-da-api-rest)
- [Instalação e Execução](#instalação-e-execução)
  - [Pré-requisitos](#pré-requisitos)
  - [Passo a Passo](#passo-a-passo)
  - [URLs de Acesso](#urls-de-acesso)
- [Povoamento de Dados (Seeds)](#povoamento-de-dados-seeds)
- [Testes Automatizados](#testes-automatizados)
  - [Pirâmide de Testes (124 testes)](#pirâmide-de-testes-124-testes)
  - [Execução dos Testes](#execução-dos-testes)
- [Comandos Úteis (Makefile)](#comandos-úteis-makefile)
- [Documentação Técnica](#documentação-técnica)

---

## Visão Geral

O projeto implementa uma loja virtual completa de ponta a ponta, focando em robustez de domínio, consistência de dados e simplicidade estrutural. Ele atende desde a navegação no catálogo até a criação definitiva do pedido, garantindo integridade transacional ACID com SQLite, desacoplamento por meio do padrão *Repository*, validação de esquemas com Pydantic v2 e interface interativa com JavaScript modular (sem frameworks pesados).

---

## Stack Tecnológica

| Camada | Tecnologias |
| :--- | :--- |
| **Backend API** | [Python 3.11+](https://www.python.org/) • [FastAPI](https://fastapi.tiangolo.com/) • [Uvicorn](https://www.uvicorn.org/) |
| **Acesso a Dados & ORM** | [SQLAlchemy 2.x](https://www.sqlalchemy.org/) • SQLite (persistido via volume Docker) |
| **Serialização & Validação** | [Pydantic v2](https://docs.pydantic.dev/) |
| **Frontend** | HTML5 • CSS3 • Vanilla JavaScript (ES6+ modular, sem build step) • Nginx |
| **Testes Automatizados** | [pytest](https://docs.pytest.org/) • [HTTPX](https://www.python-httpx.org/) (TestClient) • [Playwright](https://playwright.dev/python/) |
| **Qualidade & Linting** | [Ruff](https://beta.ruff.rs/) • [Black](https://black.readthedocs.io/) |
| **Geração de Dados Sintéticos** | [Faker](https://faker.readthedocs.io/) (`pt_BR`) |
| **Infraestrutura** | [Docker](https://www.docker.com/) • Docker Compose (v2+) • GNU Make |

---

## Arquitetura do Sistema

### Padrão em Camadas (Backend)

O backend segue rigorosamente o princípio de separação de responsabilidades em camadas unidirecionais:

```
[ Cliente HTTP / Frontend ]
          │  (Requisição REST com X-User-ID)
          ▼
   ┌──────────────┐
   │ API Routers  │  (app/api/v1/endpoints/) -> Validação de transporte, HTTP Status e serialização
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Services   │  (app/services/) -> Lógica de negócio, máquina de estados, transações ACID
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Repositories │  (app/repositories/) -> Camada exclusiva para queries ORM SQLAlchemy
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Database /   │  (app/models/ & SQLite) -> Persistência relacional
   │    Models    │
   └──────────────┘
```

- **Endpoints/Routers**: Responsáveis exclusivamente por receber requisições HTTP, delegar a execução para a camada de serviço e serializar os dados de resposta usando Schemas Pydantic. Nenhuma query SQL ou regra de negócio é executada aqui.
- **Services**: Contêm as regras de negócio puras (cálculo de descontos, transições de estado do carrinho, reserva atômica de estoque e orquestração).
- **Repositories**: Encapsulam todas as operações de banco de dados (`select`, `add`, `delete`) isolando o ORM do restante da aplicação.
- **Models & Schemas**: Classes declarativas do SQLAlchemy representando tabelas relacionais e contratos Pydantic para tipagem estrita de entrada e saída.

### Estrutura do Frontend

O frontend adota uma organização modular pura em ES6+:
- `frontend/js/api/`: Clientes HTTP assíncronos (`fetch`) consumindo os endpoints REST do backend.
- `frontend/js/domain/`: Regras de apresentação no cliente e modelos locais.
- `frontend/js/views/`: Manipulação e renderização no DOM com sanitização estrita de dados contra XSS.
- `frontend/js/utils/sanitize.js`: Funções de sanitização (`escapeHtml`, `sanitizeUrl`).
- `frontend/js/app.js`: Controlador principal que orquestra eventos do usuário, chamadas à API e renderização de estado.

### Árvore de Diretórios

```
meu-ecommerce/
├── Makefile                       # Comandos de automação do ciclo de vida
├── README.md                      # Documentação do projeto
├── AGENTS.md                      # Diretrizes técnicas para agentes de IA
├── docs/                          # Especificações funcionais, blueprints e relatórios
│   ├── scaffolding-specification.md
│   ├── seeds-report.md
│   └── carrinho/                  # Documentação detalhada da feature Carrinho
│       ├── frd-carrinho.md
│       ├── blueprint-carrinho.md
│       ├── security-report-carrinho.md
│       └── testes-carrinho.md
├── frontend/                      # Interface web (Vanilla JS + CSS)
│   ├── index.html                 # Página da loja e carrinho de compras
│   ├── css/
│   │   └── style.css              # Estilos responsivos da interface
│   └── js/
│       ├── app.js                 # Inicialização e binding de eventos
│       ├── api/                   # Clientes de comunicação com a API
│       ├── domain/                # Modelos de domínio do cliente
│       ├── utils/                 # Utilitários e sanitização contra XSS
│       └── views/                 # Renderizadores do catálogo e carrinho
└── backend/                       # Aplicação FastAPI em camadas
    ├── Dockerfile                 # Contêiner Python + Playwright headless
    ├── requirements.txt           # Dependências de produção
    ├── requirements-dev.txt       # Dependências de desenvolvimento e testes
    ├── pyproject.toml             # Configurações do linter e formatador Ruff
    ├── app/
    │   ├── main.py                # Ponto de entrada FastAPI, CORS e headers de segurança
    │   ├── database.py            # Engine SQLite e SessionLocal
    │   ├── api/                   # Injeção de dependências e roteadores REST
    │   ├── models/                # Modelos ORM (Product, Cart, CartItem, Coupon, etc.)
    │   ├── schemas/               # Modelos Pydantic (validação e DTOs)
    │   ├── repositories/          # Repositórios SQLAlchemy
    │   ├── services/              # Camada de serviços e regras de negócio
    │   └── scripts/               # Scripts de seed de dados (básico e volumétrico)
    └── tests/                     # Suíte de testes automatizados
        ├── conftest.py            # Fixtures de sessão, BD em memória e cliente HTTP
        ├── unit/                  # Testes unitários com Test Doubles desacoplados
        ├── integration/           # Testes de integração de endpoints e serviços
        └── e2e/                   # Testes ponta a ponta de API e UI com Playwright
```

---

## Funcionalidades e Regras de Negócio

### Catálogo de Produtos
- Listagem completa de produtos com título, descrição, preço e disponibilidade em estoque.
- Bloqueio automático de adição ao carrinho caso o estoque seja zero ou insuficiente.

### Carrinho de Compras e Máquina de Estados

O carrinho de compras é governado por uma **Máquina de Estados Finita**, garantindo previsibilidade e consistência ao longo de todo o ciclo de compra:

```
  ┌─────────┐
  │  EMPTY  │ ◄────────────────────────┐
  └────┬────┘                          │
       │ Adicionar primeiro item       │ Remover todos os itens
       ▼                               │
┌──────────────┐                       │
│  WITH_ITEMS  │ ──────────────────────┘
└──────┬───────┘
       │ Iniciar checkout (POST /cart/checkout)
       ▼
┌──────────────┐
│ IN_CHECKOUT  │ ── Retornar para edição (DELETE /cart/checkout) ──► [ WITH_ITEMS ]
└──────┬───────┘
       │ Confirmar pedido (POST /cart/confirm)
       ▼
┌────────────────┐
│ ORDER_CREATED  │ (Estado final irreversível)
└────────────────┘
```

- `EMPTY`: Carrinho inicial sem itens. Não permite iniciar checkout nem aplicar cupom.
- `WITH_ITEMS`: Carrinho com 1 ou mais itens. Permite alterar quantidades, remover itens e aplicar/remover cupom.
- `IN_CHECKOUT`: Carrinho congelado para revisão final de valores. Modificações de itens são bloqueadas (retorna HTTP 409 se tentar adicionar/remover itens diretamente; exige voltar para `WITH_ITEMS`).
- `ORDER_CREATED`: Pedido finalizado com sucesso. Estado terminal irreversível. Novas compras geram um novo carrinho.
- `ABANDONED`: Carrinho abandonado por desistência ou expiração (sem impacto em reservas de estoque).

### Sistema de Cupons de Desconto
- **Tipos de Desconto**: Suporte a cupons percentuais (ex: `10%`) e de valor fixo em moeda (ex: `R$ 50,00`).
- **Piso Zero**: O desconto de cupons de valor fixo é limitado ao subtotal do carrinho, impedindo totais negativos.
- **Limite**: Máximo de 1 cupom aplicado por carrinho (não-cumulativo).
- **Uso Único por Usuário**: Cada usuário pode utilizar um cupom promocional apenas uma vez em pedidos finalizados.
- **Insensibilidade a Caixa**: O código do cupom é tratado como *case-insensitive* (ex: `10off`, `10OFF` e `10Off` são idênticos).
- **Validação Temporal**: Cupons expirados são sumariamente rejeitados.

### Checkout e Confirmação Atômica de Pedidos
- A confirmação de compra (`POST /api/v1/cart/confirm`) é executada dentro de uma **transação atômica ACID**:
  1. Validação estrita do estado atual (`IN_CHECKOUT`).
  2. Verificação atômica de estoque em tempo real para cada item.
  3. Revalidação contra TOCTOU (*Time-of-Check to Time-of-Use*) da validade e uso prévio do cupom.
  4. Decremento do estoque de todos os produtos.
  5. Registro do consumo do cupom pelo usuário.
  6. Transição de estado para `ORDER_CREATED` e criação do pedido.
  7. Em caso de concorrência ou falta de estoque, a transação sofre **rollback total** e o carrinho permanece em `IN_CHECKOUT` para permitir ajustes pelo usuário.

### Hardening de Segurança (Red Team)

O projeto passou por auditoria e mitigação ativa de segurança:

1. **Controle de Acesso e Prevenção a IDOR/BOLA**: O identificador `X-User-ID` é sanitizado e validado via regex estrita (`^[a-zA-Z0-9_\-]{1,64}$`), bloqueando injeções e parâmetros maliciosos.
2. **Mitigação TOCTOU em Cupons**: A validação de expiração e uso do cupom é executada novamente na confirmação do pedido, impedindo que cupons vencidos durante a sessão sejam consumidos.
3. **Prevenção a Race Conditions**: Restrição de unicidade no banco de dados (`uq_user_coupon_usage`) impede que requisições concorrentes utilizem o mesmo cupom promocional mais de uma vez.
4. **Proteção contra XSS**: Sanitização no frontend com `escapeHtml` e `sanitizeUrl` para atributos dinâmicos e links.
5. **Headers HTTP de Segurança**:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
6. **Content-Security-Policy (CSP)**: Diretivas declaradas no HTML restringindo a execução e carregamento de scripts, estilos e conexões.
7. **Limites de Entrada**: Validação Pydantic com restrições numéricas (`quantity <= 9999`, `product_id` numérico) contra ataques de negação de serviço e *integer overflow*.

---

## Endpoints da API REST

Todas as rotas de carrinho exigem o cabeçalho HTTP obrigatório:
```http
X-User-ID: <identificador-do-usuario>
```

| Método | Endpoint | Descrição | Status de Sucesso |
| :--- | :--- | :--- | :---: |
| **GET** | `/health` | Verificação de integridade da API | `200 OK` |
| **GET** | `/api/v1/products` | Lista todos os produtos do catálogo com estoque | `200 OK` |
| **GET** | `/api/v1/cart` | Obtém o carrinho ativo do usuário ou inicializa um vazio | `200 OK` |
| **POST** | `/api/v1/cart` | Cria explicitamente um novo carrinho para o usuário | `200 OK` |
| **POST** | `/api/v1/cart/items` | Adiciona um item ao carrinho (`product_id`, `quantity`) | `200 OK` |
| **PUT** | `/api/v1/cart/items/{product_id}` | Atualiza a quantidade do item (quantidade `0` remove) | `200 OK` |
| **DELETE** | `/api/v1/cart/items/{product_id}` | Remove um item específico do carrinho | `200 OK` |
| **POST** | `/api/v1/cart/coupon` | Aplica um cupom de desconto ao carrinho | `200 OK` |
| **DELETE** | `/api/v1/cart/coupon` | Remove o cupom aplicado do carrinho | `200 OK` |
| **POST** | `/api/v1/cart/checkout` | Inicia o checkout (transiciona para `IN_CHECKOUT`) | `200 OK` |
| **DELETE** | `/api/v1/cart/checkout` | Retorna do checkout para edição (`WITH_ITEMS`) | `200 OK` |
| **POST** | `/api/v1/cart/confirm` | Confirma o pedido com baixa atômica de estoque | `200 OK` |

A documentação interativa completa (OpenAPI / Swagger e ReDoc) fica disponível quando o backend está em execução:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Instalação e Execução

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) e Docker Compose (v2+)
- [GNU Make](https://www.gnu.org/software/make/)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd meu-ecommerce
   ```

2. **Suba os contêineres da aplicação:**
   ```bash
   make up
   ```
   *Este comando constrói a imagem do backend (instalando navegadores do Playwright) e inicia o backend na porta 8000 e o frontend (Nginx) na porta 8080.*

3. **Popule a base de dados:**
   - Para o catálogo padrão de desenvolvimento e testes:
     ```bash
     make seed
     ```
   - Ou para um conjunto volumoso de dados sintéticos realistas:
     ```bash
     make seed-volume
     ```

4. **Acompanhe os logs:**
   ```bash
   make logs
   ```

5. **Para parar e remover os contêineres:**
   ```bash
   make down
   ```

### URLs de Acesso

- **Aplicação Web (Frontend):** [http://localhost:8080](http://localhost:8080)
- **API Backend:** [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Povoamento de Dados (Seeds)

O projeto possui dois scripts de povoamento do banco SQLite:

### 1. Seed Básico (`make seed`)
Adiciona o catálogo mínimo essencial de produtos e cupons utilizado como baseline para desenvolvimento e testes funcionais:
- **Produtos:** Laptop Moderno (R$ 4.500,00), Mouse Sem Fio (R$ 150,00), Teclado Mecânico (R$ 350,00).
- **Cupons:** `10OFF` (10%), `SALE10` (10%), `50FIXO` (R$ 50,00), `EXPIRADO` (retroativo para testes de erro).

### 2. Seed Volumétrico Sintético (`make seed-volume`)
Gera um catálogo realista com o auxílio do `Faker (pt_BR)` para testes de carga, benchmark e exploração da interface:
- **500 Produtos** distribuídos em 8 categorias de tecnologia (Notebooks, Monitores, Periféricos, Áudio, Armazenamento, etc.) com variações de estoque crítico, regular e sem estoque.
- **150 Cupons** (percentuais e de valor fixo, ativos e expirados).
- **1.000 Carrinhos** distribuídos em múltiplos estágios do ciclo de vida (`EMPTY`, `WITH_ITEMS`, `IN_CHECKOUT`, `ORDER_CREATED`, `ABANDONED`).
- **Mais de 2.000 Itens de Carrinho** e registros de histórico de cupons utilizados.
- Preserva a idempotência e os dados base requeridos pelos testes E2E do Playwright.

---

## Testes Automatizados

A aplicação conta com uma suíte de testes automatizados com **124 testes** e **100% de aprovação**, cobrindo todas as camadas da aplicação:

### Pirâmide de Testes (124 testes)

```
              / \
             /   \
            / E2E \           -> 11 testes UI no Navegador (Playwright / Chromium)
           /------- \
          / E2E REST \        -> 5 testes de Fluxos Completos de API
         /------------\
        /  Integração  \      -> 56 testes (Endpoints, Serviços, Segurança, Seeds)
       /----------------\
      /    Unitários     \    -> 52 testes (Regras puras, Schemas, Test Doubles)
     /--------------------\
```

- **Testes Unitários (`tests/unit/`)**: Validam regras puras de cálculo de desconto, limites de piso zero e transições de estado sem tocar em I/O nem banco de dados. Utilizam *Test Doubles* dedicados (`FakeCartRepository`, `StubProductService`, `SpyCouponService`, `MockDbSession`).
- **Testes de Integração (`tests/integration/`)**: Validam requisições HTTP via FastAPI TestClient, persistência real no SQLite em memória, garantias ACID de rollback, validação do cabeçalho `X-User-ID` e headers de segurança.
- **Testes Ponta a Ponta de API (`tests/e2e/test_api_flows.py`)**: Validam jornadas completas de múltiplos usuários, conflitos de concorrência e integridade referencial.
- **Testes Ponta a Ponta de Interface (`tests/e2e/test_cart_ui.py`)**: Utilizam o Playwright com navegador Chromium headless para testar a interface do usuário: adição de itens, manipulação de quantidades, aplicação de cupons válidos e inválidos, alertas visuais, fluxo de checkout e confirmação final com verificação no banco.

### Execução dos Testes

Execute toda a suíte de testes através do comando:
```bash
make test
```

Para rodar apenas uma categoria específica de testes dentro do contêiner:
```bash
# Apenas testes unitários
docker compose exec backend pytest tests/unit -v

# Apenas testes de integração e segurança
docker compose exec backend pytest tests/integration -v

# Apenas testes ponta a ponta com Playwright
docker compose exec backend pytest tests/e2e -v
```

---

## Comandos Úteis (Makefile)

O `Makefile` centraliza todos os comandos essenciais do ciclo de desenvolvimento:

| Comando | Descrição |
| :--- | :--- |
| `make up` | Constrói as imagens e inicia os contêineres em segundo plano (*detached*) |
| `make down` | Para e remove contêineres, redes e volumes criados pelo Compose |
| `make logs` | Exibe os logs contínuos de todos os contêineres (`tail -f`) |
| `make test` | Executa a suíte completa de testes automatizados com pytest e Playwright |
| `make format` | Executa o linter e autofix com Ruff e formatação com Black no backend |
| `make seed` | Popula o banco com os dados essenciais de produtos e cupons de teste |
| `make seed-volume` | Popula o banco com dados sintéticos volumosos realistas (~3.800 registros) |

---

## Documentação Técnica

Para aprofundamento na arquitetura, decisões técnicas e histórico de requisitos, consulte a pasta [`docs/`](./docs):

- **[scaffolding-specification.md](./docs/scaffolding-specification.md)**: Especificação original da arquitetura do projeto e listagem inicial.
- **[docs/carrinho/frd-carrinho.md](./docs/carrinho/frd-carrinho.md)**: Documento de Requisitos Funcionais (FRD) completo do carrinho de compras.
- **[docs/carrinho/blueprint-carrinho.md](./docs/carrinho/blueprint-carrinho.md)**: Blueprint técnico detalhando os modelos, schemas, endpoints e pseudo-código.
- **[docs/carrinho/security-report-carrinho.md](./docs/carrinho/security-report-carrinho.md)**: Relatório da auditoria de segurança (Red Team) com os 7 findings e correções implementadas.
- **[docs/carrinho/testes-carrinho.md](./docs/carrinho/testes-carrinho.md)**: Relatório detalhado da cobertura de testes, test doubles e cenários mapeados.
- **[docs/seeds-report.md](./docs/seeds-report.md)**: Relatório de benchmark e especificação da geração de dados sintéticos via Faker.
- **[AGENTS.md](./AGENTS.md)**: Diretrizes e restrições obrigatórias para agentes de inteligência artificial que atuam no repositório.
