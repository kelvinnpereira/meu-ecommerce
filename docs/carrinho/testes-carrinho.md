# Relatório de Testes — Carrinho de Compras

## Resumo da Suíte
- **Total de testes**: 104
- **Unitários**: 40
- **Integração (Service + ORM)**: 27
- **E2E (Endpoint REST)**: 30
- **E2E (Frontend / Playwright)**: 7
- **Taxa de sucesso**: 100% (104 passando / 104 total)
- **Tempo de execução total**: ~6.2 segundos

---

## Pirâmide de Testes

```
              / \
             /   \
            / E2E \           -> 7 testes UI (Playwright)
           /------- \
          / E2E REST \        -> 30 testes de Endpoints (TestClient)
         /------------\
        /  Integração  \      -> 27 testes de Serviços + ORM SQLite
       /----------------\
      /    Unitários     \    -> 40 testes (Schemas, Doubles, Mocks, Fakes)
     /--------------------\
```

A distribuição respeita os princípios da pirâmide de testes de software:
1. **Base larga (Unitários)**: Testes ultrarrápidos (0.1s) validando cálculos matemáticos de desconto, arredondamento para 2 casas decimais, piso zero e toda a máquina de estados desacoplada via Test Doubles.
2. **Camada Intermediária (Integração e Endpoints)**: Validação das transações ACID, decorators do SQLAlchemy, conversão e serialização HTTP no FastAPI, guards da máquina de estados e persistência real.
3. **Topo (E2E Frontend)**: Validação com navegador headless (Chromium) dos fluxos completos de adição, alteração de quantidade até zero, aplicação de cupom, checkout, retorno para edição, confirmação e alertas visuais.

---

## Cobertura de Requisitos

| Requisito / Regra | Tipo de Teste | Arquivo(s) de Teste | Status |
| :--- | :--- | :--- | :--- |
| **RF-001**: Inicializar Carrinho | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-002**: Adicionar Item | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-003**: Atualizar Quantidade | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-004**: Remover Item | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-005**: Visualizar Carrinho | Unitário, Endpoint, E2E | `test_cart_schemas_and_domain.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-006**: Aplicar Cupom | Unitário, Integração, Endpoint, E2E | `test_coupon_service.py`, `test_cart_service_unit.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-007**: Remover Cupom | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-008**: Iniciar Checkout | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-009**: Voltar para Edição | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-010**: Confirmar Pedido Atômico | Unitário, Integração, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RF-011**: Abandonar Carrinho | Unitário, Integração | `test_cart_service_unit.py`, `test_cart_service.py` | Coberto |
| **RN-001**: Limite 1 Cupom por Carrinho | Integração, Endpoint | `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-002**: Uso Único por Usuário | Unitário, Integração, Endpoint | `test_coupon_service.py`, `test_cart_service_unit.py`, `test_cart_endpoint.py` | Coberto |
| **RN-003**: Insensibilidade a Caixa | Unitário, Integração, Endpoint | `test_coupon_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-004**: Cálculo e Piso Zero | Unitário, Integração, Endpoint | `test_cart_schemas_and_domain.py`, `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-005**: Validade de Cupons | Unitário, Integração, Endpoint | `test_coupon_service.py`, `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-006**: Estoque Otimista | Unitário, Integração, Endpoint | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-007**: Rollback em Conflito | Unitário, Integração, Endpoint | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |
| **RN-008**: Validação de Quantidade | Unitário, Endpoint, E2E | `test_cart_service_unit.py`, `test_cart_endpoint.py`, `test_cart_ui.py` | Coberto |
| **RN-009**: Irreversibilidade do Pedido | Unitário, Integração, Endpoint | `test_cart_service_unit.py`, `test_cart_service.py`, `test_cart_endpoint.py` | Coberto |

---

## Test Doubles Utilizados

Localização: `backend/tests/unit/doubles.py`

| Test Double | Tipo | Responsabilidade / Dependência Simulada |
| :--- | :---: | :--- |
| **`FakeCartRepository`** | Fake | Implementação completa em memória do repositório de carrinhos (`carts_by_id`, `carts_by_user`). Elimina I/O e dependência de banco relacional nos testes unitários. |
| **`StubProductService`** | Stub | Fornece retornos controlados de produtos, consulta de preços e verificação/decremento de estoque sem acoplamento a banco. |
| **`SpyCouponService`** | Spy | Valida códigos promocionais em memória e espiona se `mark_coupon_as_used` foi chamado exatamente uma vez com o `coupon_id`, `user_id` e `order_id` corretos. |
| **`MockDbSession`** | Mock / Spy | Intercepta operações do SQLAlchemy (`add`, `delete`, `commit`, `rollback`, `refresh`). Permite comprovar se `commit()` foi invocado no sucesso e `rollback()` em cenários de falha atômica. |

---

## Seeds e Fixtures

Localização: `backend/tests/fixtures/factories.py` e `backend/tests/e2e/conftest.py`

1. **Geração Semântica com Faker**:
   - Configurada para localidade `pt_BR` com seed determinística para repetibilidade.
   - Fornece builders semânticos: `build_product()`, `build_coupon()`, `build_cart()`, `build_cart_item()`.
2. **Catálogo Representativo de Produtos**:
   - `Notebook Dell XPS 15` (R$ 8.499,90, 5 unidades) — produto premium de alto valor.
   - `Mouse Sem Fio Logitech MX Master 3S` (R$ 489,50, 25 unidades) — produto padrão de catálogo.
   - `Monitor Ultrawide LG 29WK600` (R$ 1.250,00, 1 unidade) — cenário limite de última unidade em estoque.
   - `Cadeira Ergonômica Herman Miller Aeron` (0 unidades) — cenário de produto esgotado.
3. **Catálogo Representativo de Cupons**:
   - `DESC10` (10% percentual).
   - `BLACKFRIDAY15` (15% percentual).
   - `BEMVINDO50` (R$ 50,00 fixo).
   - `MEGABONUS200` (R$ 200,00 fixo para teste de piso zero).
   - `NATALPASSADO` (cupom expirado retroativo).
4. **Isolamento de Estado**:
   - Testes de integração utilizam SQLite in-memory com `StaticPool` e fixture `clean_db`.
   - Testes E2E (Playwright) possuem fixture com `autouse=True` limpando o carrinho do usuário, restaurando estoques originais e purgando registros de `user_coupon_usages` antes e após cada cenário.

---

## Bugs Encontrados Durante os Testes

| # | Localização | Descrição do Bug | Impacto | Status |
| :---: | :--- | :--- | :--- | :---: |
| 1 | `backend/app/services/cart_service.py:108` | O método `add_item` não validava o estado `IN_CHECKOUT`, permitindo inserção de itens sem transição prévia de retorno (`return_to_cart`). | Violação da máquina de estados do FRD Seção 6. | **Corrigido** |
| 2 | `backend/app/repositories/coupon_repository.py:16` e `backend/app/schemas/coupon.py` | Códigos de cupom enviados com espaços no início ou fim (`" desc10 "`) não sofriam `strip()`, causando rejeição indevida. | Falha no cumprimento da RN-003. | **Corrigido** |
| 3 | `backend/tests/e2e/conftest.py` | O setup e teardown de E2E não removiam registros de `user_coupon_usages`, fazendo com que testes subsequentes falhassem ao tentar reutilizar cupom. | Vazamento de estado e falha de isolamento de teste. | **Corrigido** |

---

## Cenários Não Cobertos (Gaps Residuais)

1. **Abandono Automático por Timeout (Cron / Worker)**:
   - O método `abandon_cart` foi coberto em nível de serviço e integração, mas a expiração assíncrona baseada em relógio e agendamento contínuo permanece fora do escopo conforme acordado no Blueprint técnico (Seção 9).
2. **Concorrência Real Multiprocesso via PostgreSQL / MySQL**:
   - Os testes de deadlock e atomicidade validam a ordenação determinística de IDs (`sorted(items, key=lambda i: int(i.product_id))`) e simulações com transações SQLite. Testes de concorrência com threads simultâneas disputando locks pessimistas a nível de SO podem ser adicionados quando o banco de produção final for configurado.
