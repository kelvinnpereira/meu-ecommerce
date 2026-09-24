# Relatório E2E — Carrinho de Compras

## Resumo
- **Total de fluxos testados**: 6 fluxos críticos completos
- **Testes E2E executados**: 16 cenários automatizados
- **Testes passando**: 16 (100% de sucesso)
- **Testes falhando**: 0
- **Bugs encontrados**: 0 bugs novos na suíte E2E (comportamentos de concorrência, integridade atômica e bloqueios de cupom funcionando conforme especificação)
- **Tempo total de execução E2E**: ~16.7 segundos

---

## Pirâmide E2E: Camadas Exercitadas

Todos os testes foram executados com a aplicação real completa em execução (FastAPI + SQLite `ecommerce.db` + Nginx Frontend + Chromium Headless Playwright):
1. **Frontend UI (Playwright)**:
   - Renderização da página, adição de itens pelo catálogo, delegação de eventos, manipulação de inputs numéricos com re-render, disparos assíncronos contra a API REST via Nginx, modais/alertas do navegador (`page.on('dialog')`).
2. **API REST (HTTP Requests)**:
   - Rotas de produtos e carrinho (`/api/v1/products`, `/api/v1/cart/*`), cabeçalhos de identificação de usuário (`X-User-ID`), status codes HTTP (200, 404, 409, 422).
3. **Persistência Relacional (SQLite / SQLAlchemy)**:
   - Verificação direta nas tabelas `products`, `carts`, `cart_items` e `user_coupon_usages` em `ecommerce.db`, confirmando decrementos corretos, integridade transacional e rollback atômico.

---

## Fluxos Cobertos

| Fluxo | Camada Principal | Passos | Status | Observação |
| :--- | :---: | :---: | :---: | :--- |
| **Fluxo 1: Compra Completa (Happy Path)** | UI + Banco | 6 | **Passando** | Adição de múltiplos produtos, aplicação de cupom percentual `SALE10`, checkout, confirmação, reset da UI e verificação de decremento de estoque e registro de cupom no banco. |
| **Fluxo 1: Compra Completa via API** | API + Banco | 6 | **Passando** | `test_e2e_api_full_purchase_and_db_state`: valida cálculo de subtotal (R$ 4.800), desconto (R$ 480) e total (R$ 4.320), transição para `ORDER_CREATED` e bloqueio de mutações posteriores (RN-009). |
| **Fluxo 2: Edição Bidirecional com Retorno do Checkout** | UI + Banco | 6 | **Passando** | `test_e2e_ui_checkout_edit_return_and_completion`: avança para checkout (`IN_CHECKOUT`), clica em 'Voltar para Edição', ajusta quantidades e adiciona novo produto, reavançando e confirmando com decremento exato no banco. |
| **Fluxo 3: Conflito Concorrente de Estoque e Rollback Atômico** | UI + Banco | 6 | **Passando** | `test_e2e_ui_stock_conflict_rollback_and_recovery`: simula corrida de estoque concorrente enquanto usuário está no checkout. Confirmação rejeitada com alerta de estoque, rollback total no SQLite (estoque e cupom preservados). Usuário retorna, ajusta quantidade e conclui com sucesso. |
| **Fluxo 3: Conflito Concorrente e Rollback Atômico via API** | API + Banco | 5 | **Passando** | `test_e2e_api_stock_conflict_and_atomic_rollback`: valida HTTP 422 em falta de estoque no `confirm_order`, persistência intacta no banco (`status = IN_CHECKOUT`, zero usages), e conclusão após retorno (`DELETE /checkout`). |
| **Fluxo 4: Ciclo Completo de Cupons e Reuso Bloqueado na UI** | UI + Banco | 6 | **Passando** | `test_e2e_ui_coupon_lifecycle_and_reusage_blocked`: valida rejeição de cupom inexistente e expirado com alertas, aplicação de cupom de valor fixo `50FIXO`, conclusão do pedido e bloqueio imediato na tentativa de reuso pelo mesmo usuário na compra seguinte (RN-002). |
| **Fluxo 4: Ciclo de Cupons e Uso Único via API** | API + Banco | 7 | **Passando** | `test_e2e_api_coupon_validation_and_single_use`: valida HTTP 422 para inexistente e expirado, normalização de código com espaços/minúsculas (`"  50fixo  "`), substituição por `SALE10` (RN-001) e bloqueio definitivo pós-compra (RN-002). |
| **Fluxo 5: Esvaziamento do Carrinho e Desvinculação Automática** | UI + Banco | 4 | **Passando** | `test_e2e_remove_all_items_clears_coupon_and_resets_ui` e `test_decrease_quantity_to_zero_removes_item`: decremento para zero remove item; remoção do último item transiciona carrinho para `EMPTY`, remove cupom e desabilita checkout. |
| **Fluxo 6: Isolamento Multi-usuário Simultâneo** | API + Banco | 4 | **Passando** | `test_e2e_api_multi_user_isolation`: `user-e2e-a` e `user-e2e-b` operam concorrentemente sem vazamento de itens, valores ou estados. A finalização do pedido de A não afeta o carrinho aberto de B. |
| **Fluxo 6: Guardas da Máquina de Estados** | API | 3 | **Passando** | `test_e2e_api_empty_cart_guards`: checkout de carrinho vazio (HTTP 422), cupom em carrinho vazio (HTTP 422), confirmação prematura fora de checkout (HTTP 409). |
| **Fluxo Auxiliar: Listagem de Catálogo no Frontend** | UI | 2 | **Passando** | `test_product_listing_e2e`: catálogo completo de produtos exibido com nomes, descrições e preços formatados. |

---

## Bugs Encontrados
- **Nenhum bug funcional encontrado durante os testes E2E**:
  As correções arquiteturais previamente introduzidas (tratamento de exceções em `CouponService`, suporte a múltiplos pedidos por usuário via índice no `user_id`, ordenação determinística de IDs para prevenção de deadlocks e atomicidade de transações com rollback) sustentaram 100% dos cenários de ponta a ponta sem falhas.

---

## Cenários Não Cobertos
- **Abandono Automático por Timeout (Cron / Job Assíncrono)**:
  - O método de domínio `abandon_cart` está implementado e validado em nível de serviço/integração, porém o gatilho assíncrono baseado em tempo contínuo (daemon/scheduler) permanece fora do escopo funcional da sprint conforme definido no Blueprint (Seção 9).
- **Gateway de Pagamento Externo**:
  - Fora de escopo de acordo com os requisitos de alto nível (`secao_6.0.1.md`). A confirmação de compra conclui com a máquina de estados interna e criação do pedido.

---

## Arquivos Criados e Atualizados

| Arquivo | Ação | Propósito |
| :--- | :---: | :--- |
| `backend/tests/e2e/test_api_flows.py` | **Criado** | Testes de fluxos E2E via API HTTP real contra a instância do servidor e inspeção direta no banco `ecommerce.db` (compra completa, concorrência com rollback, ciclo de cupom, isolamento multi-usuário e guardas de estado). |
| `backend/tests/e2e/test_cart_ui.py` | **Atualizado** | Adicionados novos testes E2E com Playwright cobrindo persistência no SQLite pós-compra, navegação bidirecional de checkout/edição, concorrência com rollback atômico e bloqueio de reuso de cupom na UI. |
| `backend/tests/e2e/conftest.py` | **Atualizado** | Fixtures `autouse=True` de setup/teardown garantindo sementes determinísticas para cupons (`SALE10`, `50FIXO`, `EXPIRADO`), estoques consistentes e limpeza de isolamento para usuários de teste (`user-123`, `user-e2e-a`, `user-e2e-b`). |
| `docs/carrinho/e2e-report-carrinho.md` | **Criado** | Relatório completo de execução, mapeamento e rastreabilidade dos testes de ponta a ponta. |

---

## Evidência de Execução

```bash
docker compose exec backend pytest tests/e2e/ -v
```

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0 -- /usr/bin/python
cachedir: .pytest_cache
rootdir: /home/appuser/app
configfile: pyproject.toml
plugins: anyio-4.5.2, playwright-0.5.2, Faker-35.2.2, base-url-2.1.0
collected 16 items

tests/e2e/test_api_flows.py::test_e2e_api_full_purchase_and_db_state PASSED      [  6%]
tests/e2e/test_api_flows.py::test_e2e_api_stock_conflict_and_atomic_rollback PASSED [ 12%]
tests/e2e/test_api_flows.py::test_e2e_api_coupon_validation_and_single_use PASSED [ 18%]
tests/e2e/test_api_flows.py::test_e2e_api_multi_user_isolation PASSED          [ 25%]
tests/e2e/test_api_flows.py::test_e2e_api_empty_cart_guards PASSED             [ 31%]
tests/e2e/test_cart_ui.py::test_cart_full_e2e_flow[chromium] PASSED            [ 37%]
tests/e2e/test_cart_ui.py::test_decrease_quantity_to_zero_removes_item[chromium] PASSED [ 43%]
tests/e2e/test_cart_ui.py::test_e2e_checkout_and_return_to_cart_flow[chromium] PASSED [ 50%]
tests/e2e/test_cart_ui.py::test_e2e_complete_checkout_and_confirm_order[chromium] PASSED [ 56%]
tests/e2e/test_cart_ui.py::test_e2e_apply_invalid_coupon_shows_alert[chromium] PASSED [ 62%]
tests/e2e/test_cart_ui.py::test_e2e_remove_all_items_clears_coupon_and_resets_ui[chromium] PASSED [ 68%]
tests/e2e/test_cart_ui.py::test_e2e_ui_full_purchase_verifies_db_persistence[chromium] PASSED [ 75%]
tests/e2e/test_cart_ui.py::test_e2e_ui_checkout_edit_return_and_completion[chromium] PASSED [ 81%]
tests/e2e/test_cart_ui.py::test_e2e_ui_stock_conflict_rollback_and_recovery[chromium] PASSED [ 87%]
tests/e2e/test_cart_ui.py::test_e2e_ui_coupon_lifecycle_and_reusage_blocked[chromium] PASSED [ 93%]
tests/e2e/test_product_listing_ui.py::test_product_listing_e2e[chromium] PASSED [100%]

======================== 16 passed, 6 warnings in 16.68s ========================
```
