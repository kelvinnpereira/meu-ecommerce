# Blueprint Técnico — Carrinho de Compras

## 1. Contexto

### 1.1 Resumo da Funcionalidade
Este documento detalha o plano técnico para a implementação da funcionalidade de **Carrinho de Compras**. O objetivo é permitir que os usuários adicionem produtos, gerenciem quantidades, apliquem cupons de desconto e convertam o carrinho em um pedido formal, seguindo um conjunto estrito de regras de negócio e uma máquina de estados finita.

### 1.2 Arquitetura e Stack
A implementação seguirá a arquitetura existente do projeto:
- **Backend**: Python 3.11+ com FastAPI, utilizando um padrão de camadas (Endpoints, Services, Repositories).
- **Acesso a Dados**: SQLAlchemy como ORM, provavelmente sobre um banco de dados SQLite para desenvolvimento.
- **Frontend**: JavaScript puro, com uma estrutura de separação de responsabilidades (API, Domain, Views).
- **Ferramentas**: Docker Compose para orquestração, Pytest para testes, Ruff/Black para formatação.

### 1.3 Premissas Técnicas
- Um mecanismo de identificação de usuário (`user_id`) está disponível na camada de API para ser injetado nos serviços.
- O módulo de `Products` existe e fornece uma interface para consultar informações de produtos, incluindo o estoque atual.
- A criação do `Pedido` ao final do fluxo será delegada a um `OrderService` (cuja criação ou existência é um pré-requisito).

## 2. Modelos de Dados (SQLAlchemy)

Novas entidades a serem criadas em `backend/app/models/`:

- **`Coupon`**:
  - `id`: PK
  - `code`: `String`, único, indexado.
  - `discount_type`: `Enum('PERCENTAGE', 'FIXED_VALUE')`.
  - `value`: `Numeric`.
  - `expires_at`: `DateTime`.
  - `max_uses_per_user`: `Integer`, default `1`.

- **`Cart`**:
  - `id`: PK
  - `user_id`: `String`, indexado.
  - `status`: `Enum('EMPTY', 'WITH_ITEMS', 'IN_CHECKOUT', 'ORDER_CREATED', 'ABANDONED')`.
  - `coupon_id`: FK para `Coupon`, anulável.
  - `created_at`, `updated_at`: `DateTime`.

- **`CartItem`**:
  - `id`: PK
  - `cart_id`: FK para `Cart`.
  - `product_id`: `String`, referência externa.
  - `quantity`: `Integer`.
  - `unit_price`: `Numeric`.

- **`UserCouponUsage`**:
  - `user_id`: `String`
  - `coupon_id`: FK para `Coupon`
  - `order_id`: `String`.

## 3. Componentes e Módulos

- **Backend (`./backend/app/`)**:
  - **Novos Arquivos**: `models/cart.py`, `models/coupon.py`, `schemas/cart.py`, `schemas/coupon.py`, `services/cart_service.py`, `services/coupon_service.py`, `repositories/cart_repository.py`, `repositories/coupon_repository.py`, `api/v1/endpoints/cart.py`.
  - **Arquivos a Modificar**: `main.py` (para registrar o novo router).

- **Frontend (`./frontend/`)**:
  - **Novos Arquivos**: `js/api/cartApi.js`, `js/domain/cart.js`, `js/views/cartView.js`.
  - **Arquivos a Modificar**: `js/app.js`, `index.html`, `css/style.css`.

## 4. Interfaces (API Endpoints REST)

- `GET /api/v1/cart`: Visualizar carrinho.
- `POST /api/v1/cart/items`: Adicionar item.
- `PUT /api/v1/cart/items/{product_id}`: Atualizar quantidade.
- `DELETE /api/v1/cart/items/{product_id}`: Remover item.
- `POST /api/v1/cart/coupon`: Aplicar cupom.
- `DELETE /api/v1/cart/coupon`: Remover cupom.
- `POST /api/v1/cart/checkout`: Iniciar o processo de checkout.
- `POST /api/v1/cart/confirm`: Confirmar o pedido (operação atômica).

## 5. Lógica de Negócio (Pseudo-código)

A lógica crítica de **confirmação de pedido com verificação de estoque atômica** em `CartService.confirm_order()` seguirá este fluxo:
```python
# Inicia uma transação com o banco de dados (ACID)
try:
    # 1. Valida o estado do carrinho ("Em Checkout").
    # 2. Para cada item, trava a linha do produto no DB e compara estoque vs. quantidade.
    #    - Se houver falha, lança StockConflictError.
    # 3. Se houver estoque para todos, decrementa o estoque de cada produto.
    # 4. Cria o "Pedido".
    # 5. Registra o uso do cupom, se aplicável.
    # 6. Altera o status do carrinho para "Pedido Criado".
    # 7. Commita a transação.
except StockConflictError:
    # 8. Faz o rollback da transação em caso de erro.
```

## 6. Tarefas de Implementação

### Fase 1: Backend - Fundação e Modelos de Dados
- **T-001**: Definir Modelos SQLAlchemy (`Cart`, `CartItem`, `Coupon`, `UserCouponUsage`).
- **T-002**: Configurar Migração de Banco de Dados e Criar Tabelas.
- **T-003**: Criar Schemas Pydantic (`CartRead`, `CartItemCreate`, etc.).
- **T-004**: Implementar Repositórios Básicos (`CartRepository`, `CouponRepository`).

### Fase 2: Backend - Lógica Principal do Carrinho
- **T-005**: Implementar Serviço de Visualização e Criação do Carrinho.
- **T-006**: Implementar Adição de Itens ao Carrinho.
- **T-007**: Implementar Atualização e Remoção de Itens.

### Fase 3: Backend - Lógica de Cupons
- **T-008**: Popular Dados de Cupons (Seed).
- **T-009**: Implementar Serviço de Validação de Cupom.
- **T-010**: Implementar Aplicação e Remoção de Cupom no Carrinho.

### Fase 4: Backend - Máquina de Estados e Checkout
- **T-011**: Implementar Transições de Estado para Checkout (`Em Checkout` <-> `Com Itens`).
- **T-012**: Implementar Confirmação de Pedido Atômica.

### Fase 5: Backend - API e Integração
- **T-013**: Criar Endpoints da API do Carrinho no FastAPI.

### Fase 6: Frontend - Estrutura e API
- **T-014**: Criar Estrutura HTML/CSS do Carrinho.
- **T-015**: Implementar Módulo `cartApi.js` para consumir a API.

### Fase 7: Frontend - Interatividade e Visualização
- **T-016**: Implementar Lógica de Domínio e Visualização do Carrinho (`cart.js`, `cartView.js`).
- **T-017**: Conectar Ações do Usuário na UI à API.

## 7. Matriz de Rastreabilidade

| Requisito | Tarefa(s) Correspondente(s) |
| :--- | :--- |
| RF-001 | T-005 |
| RF-002 | T-006 |
| RF-003 | T-007 |
| RF-004 | T-007 |
| RF-005 | T-005, T-013, T-016 |
| RF-006 | T-010 |
| RF-007 | T-010 |
| RF-008 | T-011 |
| RF-009 | T-011 |
| RF-010 | T-012 |
| RN-001 | T-010 |
| RN-002 | T-001, T-009, T-012 |
| RN-003 | T-009 |
| RN-004 | T-005, T-010 |
| RN-005 | T-009 |
| RN-006 | T-012 |
| RN-007 | T-012 |
| RN-008 | T-006, T-007 |
| RN-009 | T-011, T-012 |

## 8. Riscos e Pontos de Atenção
- A implementação da transação atômica em **T-012** é a parte mais crítica e deve ser testada exaustivamente, incluindo cenários de concorrência se possível.
- A dependência de um `OrderService` para a criação do pedido precisa ser resolvida.

## 9. Fora do Escopo Técnico
- **RF-011 (Abandonar Carrinho)**: A funcionalidade de limpar carrinhos abandonados por inatividade não está incluída neste plano, pois requer um processo assíncrono (ex: cron job), sendo melhor tratada como uma feature separada.
