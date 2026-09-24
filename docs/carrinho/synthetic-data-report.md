# Relatório de Dados Sintéticos — Feature Carrinho & Benchmark de Carga

## 1. Resumo Executivo
- **Data da Execução:** 24/09/2026
- **Contexto:** Geração volumosa de dados sintéticos realistas para testes de carga, integração e validação funcional de ponta a ponta.
- **Entidades Populadas:** 5 entidades relacionais (`Product`, `Coupon`, `Cart`, `CartItem`, `UserCouponUsage`)
- **Total de Registros Gerados no Banco:** 3.867 registros
- **Biblioteca Utilizada:** `Faker` (versão 40.39.0, locale `pt_BR`) com catálogos semânticos de e-commerce e regras de negócio estritas.

## 2. Dados Gerados por Entidade

| Entidade | Registros | Variações e Cenários Cobertos | Observações e Integridade |
| :--- | :--- | :--- | :--- |
| **`Product`** | **500** | • 8 categorias de tecnologia (Notebooks, Monitores, Periféricos, Áudio, Armazenamento, Redes/IoT, Cabos, Ergonomia).<br>• Preços de R$ 44,00 a R$ 14.948,49 (média de R$ 2.595,26).<br>• Estoque: 25 sem estoque (5%), 67 estoque crítico (13.4%), 356 estoque regular (71.2%), 52 alto volume (10.4%).<br>• 69 produtos com descrição nula (13.8%) e 431 com especificações técnicas completas. | Preservou os 3 produtos base (`Laptop Moderno`, `Mouse Sem Fio Ergonômico`, `Teclado Mecânico RGB`) requeridos pelos testes E2E do Playwright. |
| **`Coupon`** | **150** | • Tipos: 92 percentuais (5% a 70%) e 58 de valor fixo (R$ 10,00 a R$ 500,00).<br>• Validade: 118 ativos futuros e 32 expirados no passado.<br>• Limite de uso por usuário: 1 a 5 utilizações. | Preservou os 4 cupons base (`10OFF`, `SALE10`, `50FIXO`, `EXPIRADO`). |
| **`Cart`** | **1.000** | • Status do ciclo de vida:<br>  - `EMPTY`: 150 (15%)<br>  - `WITH_ITEMS`: 350 (35%)<br>  - `IN_CHECKOUT`: 150 (15%)<br>  - `ORDER_CREATED`: 250 (25%)<br>  - `ABANDONED`: 100 (10%)<br>• Distribuídos entre ~750 usuários únicos ao longo dos últimos 90 dias. | Idempotência e chaves primárias validadas. Cupons atribuídos respeitando estados e limites. |
| **`CartItem`** | **2.076** | • 1 a 8 itens distintos por carrinho não-vazio.<br>• Quantidades variando entre 1 e 4 (95%) e 5 a 25 para compras em lote/atacado (5%).<br>• Preço unitário snapshot fiel ao valor do produto na criação. | Zero itens órfãos (100% dos `product_id` mapeiam produtos reais existentes). |
| **`UserCouponUsage`**| **141** | • Gerados para pedidos confirmados (`ORDER_CREATED`) com cupom.<br>• Formato de pedido: `ORD-2026-XXXXXX`. | Zero utilizações órfãs; limites `max_uses_per_user` estritamente respeitados. |

## 3. Estrutura e Execução dos Seeds
- **Arquivo Principal:** `backend/app/scripts/seed_volume.py`
- **Comando Local:**
  ```bash
  cd backend && DATABASE_URL="sqlite:///./ecommerce.db" PYTHONPATH=. python -m app.scripts.seed_volume --clean
  ```
- **Comando Docker:**
  ```bash
  make seed-volume
  ```
- **Parâmetros Suportados:**
  - `--clean`: limpa as tabelas respeitando a ordem relacional reversa antes de povoar.
  - `--products`: define o target de produtos (padrão: 500).
  - `--coupons`: define o target de cupons (padrão: 150).
  - `--carts`: define o target de carrinhos (padrão: 1000).
- **Idempotência:** A re-execução sem `--clean` detecta a volumetria existente e não duplica dados nem viola restrições de unicidade.

## 4. Validação e Testes
- **Testes Automatizados:** 99/99 testes passando com sucesso (`pytest tests/unit tests/integration`), incluindo a nova suíte `tests/integration/test_seed_volume.py`.
- **Integridade Relacional:**
  - `CartItem -> Product`: 0 registros órfãos.
  - `UserCouponUsage -> Coupon`: 0 registros órfãos.
- **Operação da Aplicação (FastAPI):**
  - `GET /health`: 200 OK (`{"status": "ok"}`)
  - `GET /api/v1/products`: 200 OK (500 produtos retornados em JSON serializado)
  - `GET /api/v1/cart`: 200 OK (manipulação e criação de carrinhos operando normalmente)
