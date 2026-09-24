# Relatório de Revisão — Carrinho de Compras

## Resumo Executivo
- **Total de findings**: 13 (2 críticos, 3 altos, 5 médios, 3 baixos)
- **Conformidade com o Blueprint**: Média (fluxo de checkout não conectado no frontend; modelo de dados definiu restrição única indevida; endpoints e serviços principais implementados)
- **Conformidade com o FRD**: Média (exceções de cupom não capturadas gerando HTTP 500; bloqueio de novo carrinho após pedido; ausência de retorno do nome do produto no item do carrinho; edge cases com status HTTP divergentes)
- **Cobertura de testes**: Parcial (ausência de testes de integração para cupons expirados/usados no endpoint, ausência de testes de rollback transacional em conflito de estoque no checkout e fluxo pós-conversão)
- **Avaliação de segurança e concorrência**: Riscos moderados (ausência de ordenação determinística de row-locks em `confirm_order` criando risco de deadlock; ausência de restrição única composta em `user_coupon_usages`)

---

## Findings

### [CRÍTICO] Exceções de Cupom Expirado e Já Utilizado Resultam em Erro HTTP 500
- **Eixo**: FRD / Boas Práticas / Tratamento de Erros
- **Localização**: `backend/app/services/coupon_service.py:9-16`, `backend/app/api/v1/endpoints/cart.py:108-112, 165-170`
- **RF/RN relacionado**: RF-006, RN-002, RN-005, FRD Seção 7 (Edge Cases)
- **Problema**: As classes `CouponExpiredError` e `CouponAlreadyUsedError` herdam diretamente de `Exception`, em vez de herdarem de `InvalidCouponError`. Nos endpoints `POST /api/v1/cart/coupon` e `POST /api/v1/cart/confirm`, o bloco `try/except` captura unicamente `(InvalidCouponError, CartEmptyError)`. Consequentemente, a tentativa de aplicar um cupom expirado ou já utilizado pelo usuário lança uma exceção não tratada no FastAPI, resultando em resposta HTTP 500 (Internal Server Error), violando a especificação do FRD que exige HTTP 422 Unprocessable Entity.
- **Recomendação**: Fazer `CouponExpiredError` e `CouponAlreadyUsedError` herdarem de `InvalidCouponError`, garantindo que sejam capturadas nos endpoints e retornem HTTP 422 com mensagens descritivas.

---

### [CRÍTICO] Restrição `unique=True` em `Cart.user_id` Bloqueia Novos Carrinhos Pós-Compra
- **Eixo**: Blueprint / FRD / Modelagem de Dados
- **Localização**: `backend/app/models/cart.py:22`, `backend/app/repositories/cart_repository.py:14-19`, `backend/alembic/versions/5ec7ade18b3f_add_cart_and_coupon_tables.py:59`
- **RF/RN relacionado**: RF-001, RN-009
- **Problema**: A coluna `Cart.user_id` foi modelada com `unique=True` na tabela e na migration, enquanto o Blueprint especificava apenas `user_id: String, indexado`. Além disso, `CartRepository.get_by_user_id` retorna o primeiro carrinho encontrado sem filtrar por status ativo. Uma vez que o carrinho é convertido em pedido (`ORDER_CREATED` — estado irreversível), qualquer nova chamada a `get_or_create_cart` retorna o carrinho finalizado e lança `InvalidTransitionError` em mutações, impedindo o usuário de criar um novo carrinho e realizar compras futuras.
- **Recomendação**: Remover a restrição `unique=True` de `Cart.user_id` no modelo e migration (mantendo apenas `index=True`). Alterar o repositório para consultar carrinhos ativos (`status IN ('EMPTY', 'WITH_ITEMS', 'IN_CHECKOUT')`), criando um novo carrinho caso o usuário não possua nenhum carrinho ativo.

---

### [ALTO] Fluxo de Checkout e Confirmação Não Conectado na UI do Frontend
- **Eixo**: Blueprint / FRD / Frontend
- **Localização**: `frontend/js/app.js`, `frontend/js/api/cartApi.js`, `frontend/index.html:48`
- **RF/RN relacionado**: RF-008, RF-009, RF-010, Tarefas T-015 e T-017 do Blueprint
- **Problema**: O botão `<button id="checkout-btn">Finalizar Compra</button>` está presente no DOM, mas não possui nenhum event listener registrado em `app.js`. O cliente HTTP `cartApi.js` não implementa as funções para consumir os endpoints de checkout (`POST /checkout`, `DELETE /checkout`, `POST /confirm`). O usuário não consegue iniciar o checkout ou concluir o pedido pela interface gráfica.
- **Recomendação**: Implementar em `cartApi.js` as funções `startCheckout`, `returnToCart` e `confirmOrder`. Adicionar handlers em `app.js` e atualizar `cartView.js` para alternar os estados do botão e informar o cliente sobre a conclusão do pedido.

---

### [ALTO] Ausência de Teste de Rollback por Falta de Estoque na Confirmação (RN-007)
- **Eixo**: Blueprint / FRD / Qualidade (Testes)
- **Localização**: `backend/tests/integration/test_cart_endpoint.py`, `backend/tests/integration/test_cart_service.py`
- **RF/RN relacionado**: RF-010, RN-006, RN-007, Tarefa T-012 do Blueprint
- **Problema**: O Blueprint identifica a atomicidade da confirmação de pedido como a operação mais crítica do sistema. Apesar de o rollback estar codificado no bloco transacional de `CartService.confirm_order`, não há nenhum teste automatizado que comprove que, se um dos itens ficar sem estoque no momento da conversão, a transação reverte, o estoque dos outros itens é preservado, o cupom não é consumido e o carrinho permanece em `IN_CHECKOUT`.
- **Recomendação**: Adicionar testes de integração simulando falha de estoque durante `confirm_order` nas camadas de serviço e endpoint.

---

### [ALTO] Falta de Validação de Guarda de Estado no Método `return_to_cart`
- **Eixo**: FRD / Máquina de Estados
- **Localização**: `backend/app/services/cart_service.py:255-263`
- **RF/RN relacionado**: RF-009, FRD Seção 6
- **Problema**: O método `return_to_cart` altera o status do carrinho diretamente para `WITH_ITEMS` sem validar se o estado atual é `IN_CHECKOUT`. Como o dicionário `_TRANSITIONS` permite a transição a partir de `EMPTY`, a invocação indevida de `return_to_cart` em um carrinho vazio o transiciona incorretamente para `WITH_ITEMS` com 0 itens.
- **Recomendação**: Validar expressamente em `return_to_cart` se `cart.status == CartStatusEnum.IN_CHECKOUT`. Caso contrário, lançar `InvalidTransitionError`.

---

### [MÉDIO] Schema `CartItemRead` Não Retorna o Nome do Produto (RF-005)
- **Eixo**: FRD / Interfaces
- **Localização**: `backend/app/schemas/cart.py:31-42`, `backend/app/models/cart.py:38-46`, `frontend/js/views/cartView.js:33-40`
- **RF/RN relacionado**: RF-005
- **Problema**: O FRD RF-005 estipula que a visualização do carrinho deve retornar lista de itens contendo ID, nome, preço unitário, quantidade e subtotal. O schema `CartItemRead` não expõe o nome do produto, obrigando o frontend a manter um mapa em memória (`productsMap`) para resolver os nomes.
- **Recomendação**: Adicionar o campo `product_name` / `name` no schema e no serviço para cumprir o contrato de visualização do carrinho.

---

### [MÉDIO] Risco de Deadlock em Concorrência no Bloqueio de Estoque
- **Eixo**: Boas Práticas / Concorrência
- **Localização**: `backend/app/services/cart_service.py:277-293`
- **RF/RN relacionado**: RF-010, RN-006, RN-007
- **Problema**: Em `confirm_order`, as linhas dos produtos são bloqueadas via `SELECT FOR UPDATE` na ordem arbitrária dos itens do carrinho. Em cenários de múltiplos usuários finalizando compras simultâneas contendo os mesmos produtos em ordens distintas, há risco iminente de deadlock no banco relacional.
- **Recomendação**: Ordenar os itens pelo ID numérico do produto (`sorted(cart.items, key=lambda i: int(i.product_id))`) antes de adquirir os locks.

---

### [MÉDIO] Consulta e Bloqueio Redundantes em `decrement_stock`
- **Eixo**: Boas Práticas / Performance
- **Localização**: `backend/app/services/cart_service.py:286-290`, `backend/app/services/product_service.py:27-37`
- **RF/RN relacionado**: RF-010
- **Problema**: `confirm_order` itera duas vezes sobre os itens: primeiro bloqueia e valida o estoque chamando `get_product_by_id_for_update`; depois chama `decrement_stock`, que executa novamente `get_product_by_id_for_update` para o mesmo produto.
- **Recomendação**: Decrementar a quantidade diretamente sobre os objetos de produto já carregados e bloqueados na primeira iteração.

---

### [MÉDIO] Ausência de Constraint Única Composta em `UserCouponUsage`
- **Eixo**: Segurança / Integridade de Dados
- **Localização**: `backend/app/models/coupon.py:28-36`, Migration `5ec7ade18b3f`
- **RF/RN relacionado**: RN-002
- **Problema**: A verificação de uso de cupom é feita apenas via query aplicacional. Não há constraint única composta `(user_id, coupon_id)` no banco de dados. Requisições simultâneas concorrentes do mesmo usuário podem ultrapassar a verificação e gravar dois usos do mesmo cupom.
- **Recomendação**: Adicionar constraint `UniqueConstraint("user_id", "coupon_id", name="uq_user_coupon")`.

---

### [MÉDIO] Status HTTP Divergente para Produto Não Encontrado na Adição (422 vs 404)
- **Eixo**: FRD / Interfaces
- **Localização**: `backend/app/api/v1/endpoints/cart.py:47-49`
- **RF/RN relacionado**: FRD Seção 7 ("Produto desativado/removido do catálogo")
- **Problema**: A rota `POST /api/v1/cart/items` captura `ProductNotFoundError` e retorna HTTP 422, enquanto a tabela de Edge Cases do FRD especifica código HTTP 404 Not Found para produtos não encontrados ou desativados.
- **Recomendação**: Ajustar o endpoint para mapear `ProductNotFoundError` para HTTP 404.

---

### [BAIXO] Schema de Entrada de Cupom (`CouponApply`) Sem Validações Estritas
- **Eixo**: FRD / Validação de Dados
- **Localização**: `backend/app/schemas/coupon.py:25-26`
- **RF/RN relacionado**: FRD Seção 5
- **Problema**: `CouponApply` aceita qualquer string. O FRD exige tamanho de 1 a 50 caracteres, conteúdo alfanumérico e sem espaços.
- **Recomendação**: Adicionar validações de regex e comprimento no Pydantic.

---

### [BAIXO] Mensagens de Erro em Inglês Divergentes do Padrão do FRD
- **Eixo**: FRD / Qualidade
- **Localização**: `backend/app/services/cart_service.py`, `backend/app/services/coupon_service.py`
- **RF/RN relacionado**: FRD Seção 7
- **Problema**: As mensagens de exceção estão em inglês (ex.: `"Insufficient stock for product..."`), enquanto o FRD especifica mensagens padronizadas em português.
- **Recomendação**: Alinhar gradualmente as mensagens para o padrão do FRD mantendo compatibilidade com testes existentes.

---

### [BAIXO] Endpoint de Abandono de Carrinho Inexistente na API
- **Eixo**: Blueprint / FRD
- **Localização**: `backend/app/api/v1/endpoints/cart.py`
- **RF/RN relacionado**: RF-011
- **Problema**: O serviço contém `CartService.abandon_cart`, mas não há rota correspondente (`POST /api/v1/cart/abandon`) para que o usuário ou um processo externo possa solicitar o abandono explícito.
- **Recomendação**: Expor a rota `POST /abandon` caso o abandono sob demanda do cliente seja requerido.

---

## Matriz de Cobertura de Requisitos

| Requisito / Regra | Implementado? | Testado? | Observação / Status |
| :--- | :--- | :--- | :--- |
| **RF-001** (Inicializar Carrinho) | Sim (com defeito) | Sim | Bloqueia segundo carrinho após pedido criado (unique user_id) |
| **RF-002** (Adicionar Item) | Sim | Sim | Funcionalidade completa; status de produto ausente retorna 422 em vez de 404 |
| **RF-003** (Atualizar Quantidade) | Sim | Sim | Reduzir para 0 remove item corretamente |
| **RF-004** (Remover Item) | Sim | Sim | Desassocia cupom se esvaziar carrinho |
| **RF-005** (Visualizar Carrinho) | Parcial | Sim | Não inclui `product_name` no item retornado |
| **RF-006** (Aplicar Cupom) | Sim (com defeito) | Parcial | Erro 500 para cupons expirados ou já utilizados |
| **RF-007** (Remover Cupom) | Sim | Sim | Remove cupom e recalcula totais |
| **RF-008** (Iniciar Checkout) | Backend apenas | Backend | Frontend não possui evento no botão de checkout |
| **RF-009** (Voltar para Edição) | Backend apenas | Backend | Falta guarda de estado em `return_to_cart`; ausente no frontend |
| **RF-010** (Confirmar Pedido) | Backend apenas | Parcial | Falta teste de rollback em conflito de estoque; ausente no frontend |
| **RF-011** (Abandonar Carrinho) | Serviço apenas | Não | Não exposto via endpoint REST |
| **RN-001** (Limite 1 cupom) | Sim | Sim | Substitui cupom anterior ou recusa |
| **RN-002** (Uso único de cupom) | Sim (com defeito) | Parcial | Gera erro 500 via HTTP em vez de 422 |
| **RN-003** (Insensibilidade a caixa) | Sim | Sim | Tratado via `func.upper()` no repositório |
| **RN-004** (Cálculo e piso zero) | Sim | Sim | Trunca total no piso zero adequadamente |
| **RN-005** (Validade de cupom) | Sim (com defeito) | Parcial | Gera erro 500 via HTTP em vez de 422 |
| **RN-006** (Estoque otimista) | Sim | Sim | Sem reserva prévia; decremento apenas no confirm |
| **RN-007** (Rollback em conflito) | Sim | Não | Falta teste automatizado de rollback transacional |
| **RN-008** (Validação de quantidade) | Sim | Sim | `quantity >= 1` validado pelo Pydantic e service |
| **RN-009** (Irreversibilidade pedido) | Sim (com defeito) | Sim | Transição irreversível respeitada, mas impede novo carrinho posterior |

---

## O que está correto
- **Arquitetura em Camadas**: Separação clara entre Models, Repositories, Services, Schemas e Endpoints.
- **Máquina de Estados Finita**: As transições de status do carrinho seguem rigorosamente a matriz do Blueprint e do diagrama da seção 6.0.1, garantindo a irreversibilidade do estado `ORDER_CREATED`.
- **Cálculo de Descontos (RN-004)**: Tratamento correto de cupons percentuais e de valor fixo, garantindo que o desconto não ultrapasse o subtotal e o total nunca seja negativo.
- **Estratégia de Estoque Otimista (RN-006)**: Não há bloqueio antecipado de estoque ao adicionar itens, e o decremento ocorre atomicamente na confirmação.
- **Conexão Frontend-Backend em Operações Básicas**: Listagem de catálogo, inserção/remoção de produtos, alteração de quantidade e aplicação de cupom possuem cobertura E2E com Playwright e funcionam com atualização de interface e prevenção de concorrência local.

---

## Próximos Passos Sugeridos (Prioridade de Execução)
1. **[Prioridade 1]** Corrigir a hierarquia de exceções de cupom para retornar HTTP 422 em cupons expirados e reutilizados.
2. **[Prioridade 1]** Remover a restrição `unique=True` em `Cart.user_id` e atualizar o repositório para permitir novos carrinhos pós-pedido.
3. **[Prioridade 2]** Conectar as ações de checkout e confirmação de pedido no frontend (`cartApi.js`, `app.js`, `cartView.js`).
4. **[Prioridade 2]** Implementar testes de integração para rollback por falta de estoque (RN-007) e guards de `return_to_cart`.
5. **[Prioridade 3]** Ordenar locks por `product_id` em `confirm_order` para mitigar deadlocks e otimizar queries redundantes.
