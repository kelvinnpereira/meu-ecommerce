# FRD Reverso — Carrinho de Compras

> **Nota de Engenharia Reversa**: Este documento foi extraído exclusivamente a partir da análise estrita do código-fonte da **Camada de Service do Backend** (`cart_service.py`, `coupon_service.py`, `product_service.py`) e da **Camada de Domain do Frontend** (`cart.js`, `product.js`), sem consulta prévia a qualquer especificação original ou blueprint.

---

## 1. Visão Geral

A funcionalidade do **Carrinho de Compras** é responsável por gerenciar a seleção de produtos por um usuário, o controle de quantidades, a associação de cupons promocionais e o ciclo de transição de estados até a finalização da compra ou abandono do carrinho.

A camada de serviço do backend implementa o fluxo de persistência e validação transacional das operações, garantindo controle de concorrência com travas pessimistas (*pessimistic locking*) na confirmação de pedidos e integridade no consumo de estoque e cupons. No frontend, a camada de domínio padroniza a estrutura de dados recebida do servidor e normaliza valores monetários e totais.

---

## 2. Atores

- **Usuário / Cliente (`user_id: str`)**: Consumidor que adiciona itens, altera quantidades, aplica/remove cupons, entra no checkout, retorna para edição ou confirma a conversão do carrinho em pedido.
- **Sistema / Rotina de Ciclo de Vida**: Agente ou rotina capaz de transicionar carrinhos inativos para o estado abandonado (`ABANDONED`).

---

## 3. Requisitos Funcionais Inferidos

- **RF-R001 — Obtenção ou Criação de Carrinho por Usuário**:
  O sistema recupera o carrinho ativo do usuário identificado por `user_id`. Caso não exista carrinho associado, um novo carrinho é criado automaticamente. Existe também método explícito para criação direta de carrinho.
  - *Origem*: `CartService.get_or_create_cart`, `CartService.create_cart`.

- **RF-R002 — Adição de Produto ao Carrinho**:
  O sistema adiciona um produto ao carrinho informando `product_id` e `quantity`. Se o produto já constar no carrinho, a quantidade solicitada é incrementada na quantidade existente. O preço unitário atual do produto é capturado e gravado no item. O estado do carrinho é alterado para `WITH_ITEMS`.
  - *Origem*: `CartService.add_item`.

- **RF-R003 — Atualização de Quantidade de Item**:
  O sistema atualiza a quantidade de um item já existente no carrinho para um novo valor absoluto. Se a nova quantidade informada for zero (`0`), o item é removido do carrinho.
  - *Origem*: `CartService.update_item`.

- **RF-R004 — Remoção de Item do Carrinho**:
  O sistema remove um item específico do carrinho através do `product_id`. Se a remoção esvaziar a lista de itens, o status do carrinho transita para `EMPTY` e qualquer cupom aplicado é desvinculado.
  - *Origem*: `CartService.remove_item`.

- **RF-R005 — Aplicação de Cupom de Desconto**:
  O sistema valida e associa um cupom de desconto ao carrinho através do seu código (`coupon_code`). O cupom só pode ser aplicado se o carrinho possuir itens, não estiver expirado e ainda não tiver sido utilizado pelo usuário.
  - *Origem*: `CartService.apply_coupon`, `CouponService.validate_coupon`.

- **RF-R006 — Remoção de Cupom de Desconto**:
  O sistema remove o cupom associado ao carrinho. Caso o carrinho não tenha cupom vinculado, a operação é executada de forma idempotente sem disparar erro.
  - *Origem*: `CartService.remove_coupon`.

- **RF-R007 — Início do Fluxo de Checkout**:
  O sistema avança o carrinho para o estado `IN_CHECKOUT`, desde que o carrinho contenha ao menos um item.
  - *Origem*: `CartService.start_checkout`.

- **RF-R008 — Retorno do Checkout para Edição do Carrinho**:
  O sistema permite reverter o status de um carrinho em `IN_CHECKOUT` para `WITH_ITEMS`, permitindo que o usuário retome a edição de produtos e cupons.
  - *Origem*: `CartService.return_to_cart`.

- **RF-R009 — Confirmação do Pedido e Baixa Transacional de Estoque**:
  O sistema confirma a compra a partir do estado `IN_CHECKOUT` executando uma transação atômica que:
  1. Ordena os itens por ID do produto para mitigar risco de deadlock.
  2. Bloqueia as linhas dos produtos no banco (`SELECT FOR UPDATE`).
  3. Revalida a disponibilidade de estoque para todos os itens.
  4. Debita o estoque de cada produto correspondente.
  5. Registra o uso do cupom associado (se existente).
  6. Transiciona o status do carrinho para `ORDER_CREATED`.
  7. Realiza rollback total em caso de indisponibilidade de estoque, erro de cupom ou falhas de integridade.
  - *Origem*: `CartService.confirm_order`.

- **RF-R010 — Abandono de Carrinho**:
  O sistema permite marcar o carrinho como `ABANDONED` a partir de estados válidos no ciclo de vida.
  - *Origem*: `CartService.abandon_cart`.

- **RF-R011 — Normalização de Estrutura de Carrinho no Cliente**:
  A classe cliente do carrinho normaliza payloads recebidos da API, aceitando objetos com `totals` aninhado (`subtotal`, `discount`, `total`) ou campos no nível raiz do objeto, convertendo-os para números decimais com fallback para zero.
  - *Origem*: `frontend/js/domain/cart.js`.

---

## 4. Regras de Negócio Inferidas

- **RN-R001 — Quantidade Mínima para Adição de Item**:
  Ao adicionar um item, `quantity` deve ser um inteiro estritamente positivo (`quantity > 0`). Valores menores ou iguais a zero disparam `ValueError("Quantity must be a positive integer.")`.

- **RN-R002 — Quantidade Não Negativa na Atualização**:
  Ao atualizar a quantidade de um item, `quantity` deve ser maior ou igual a zero (`quantity >= 0`). Valores negativos disparam `ValueError("Quantity must be a non-negative integer.")`.

- **RN-R003 — Remoção Automática por Quantidade Zero**:
  Se na chamada de atualização de item a quantidade informada for igual a `0`, a execução é automaticamente desviada para o método de remoção (`remove_item`).

- **RN-R004 — Validação de Existência do Produto no Catálogo**:
  Nas operações de adição e atualização, o `product_id` deve ser conversível para inteiro e corresponder a um produto existente no catálogo via `ProductService`. Caso contrário, dispara `ProductNotFoundError`.

- **RN-R005 — Validação Prévia de Estoque na Adição e Atualização**:
  - Na adição: a quantidade final (`quantidade já no carrinho + quantidade adicionada`) não pode exceder o estoque disponível (`product.stock`).
  - Na atualização: a nova quantidade absoluta não pode exceder o estoque disponível.
  - Se insuficiente, dispara `InsufficientStockError(product_id, requested, available)`.

- **RN-R006 — Bloqueio de Alteração em Estados Restritivos**:
  Não é permitido adicionar itens, atualizar quantidades, remover itens, aplicar cupons ou remover cupons quando o carrinho estiver nos estados `ORDER_CREATED` ou `IN_CHECKOUT`. Dispara `InvalidTransitionError(cart.status, cart.status)`.

- **RN-R007 — Existência Obrigatória do Item no Carrinho**:
  Para atualizar quantidade ou remover item, o `product_id` deve constar na coleção `cart.items`. Caso contrário, dispara `CartItemNotFoundError(product_id)`.

- **RN-R008 — Transição para Vazio e Desassociação Automática de Cupom**:
  Quando a remoção de um item esvaziar a lista de itens do carrinho (`not cart.items`), o status do carrinho é alterado automaticamente para `EMPTY` e o campo `coupon_id` é redefinido para `None`.

- **RN-R009 — Restrição de Cupom em Carrinho Vazio**:
  Não é permitido aplicar cupom promocional em um carrinho com status `EMPTY`. Dispara `CartEmptyError("Cannot apply a coupon to an empty cart.")`.

- **RN-R010 — Validação de Existência de Cupom**:
  O código do cupom informado deve existir na base de dados. Caso contrário, dispara `InvalidCouponError("Coupon does not exist.")`.

- **RN-R011 — Validação Temporal de Expiração de Cupom**:
  A data/hora de expiração do cupom (`expires_at`) deve ser posterior ao momento atual (avaliado em UTC, respeitando timezone se presente). Caso expirado, dispara `CouponExpiredError("Coupon has expired.")`.

- **RN-R012 — Unicidade de Uso do Cupom por Usuário**:
  Um cupom não pode ser aplicado nem consumido se o repositório acusar registro prévio de uso para a combinação `(user_id, coupon_id)`. Dispara `CouponAlreadyUsedError("Coupon has already been used by this user.")`.

- **RN-R013 — Idempotência na Remoção de Cupom**:
  A remoção de cupom em um carrinho que já não possui cupom associado (`cart.coupon_id is None`) é uma operação neutra e retorna o carrinho sem gerar erro.

- **RN-R014 — Exigência de Itens para Iniciar Checkout**:
  O carrinho deve possuir pelo menos um item (`bool(cart.items) == True`) para permitir o avanço para checkout. Caso vazio, dispara `CartEmptyError("Cannot start checkout with an empty cart.")`.

- **RN-R015 — Exigência de Estado IN_CHECKOUT para Confirmação**:
  A confirmação do pedido (`confirm_order`) exige estritamente que o carrinho esteja no estado `IN_CHECKOUT`. Dispara `InvalidTransitionError(cart.status, CartStatusEnum.ORDER_CREATED)` caso chamado em outro estado.

- **RN-R016 — Exigência de Itens na Confirmação de Pedido**:
  Mesmo estando em checkout, se a lista de itens estiver vazia, a confirmação é rejeitada com `CartEmptyError("Cannot confirm an order with an empty cart.")`.

- **RN-R017 — Ordenação Determinística contra Deadlock**:
  Na confirmação do pedido, os itens do carrinho são previamente ordenados de forma crescente por `int(product_id)` antes da aquisição de bloqueios de linha (`SELECT FOR UPDATE`), eliminando deadlocks entre transações concorrentes.

- **RN-R018 — Bloqueio Pessimista e Revalidação Concorrente de Estoque**:
  Durante a confirmação do pedido, cada produto é bloqueado via `get_product_by_id_for_update`. O estoque é revalidado com lock ativo. Havendo estoque suficiente, o débito (`product.stock -= quantity`) é executado dentro da transação atômica. Se algum item falhar, ocorre rollback de todos os débitos.

- **RN-R019 — Consumo Definitivo de Cupom na Confirmação**:
  Se o carrinho possuir cupom associado na confirmação, o cupom é revalidado e tem seu registro de utilização gravado com `order_id="some_order_id"`. Se ocorrer violação de unicidade (`IntegrityError`), a transação sofre rollback e dispara `CouponAlreadyUsedError("Coupon has already been used.")`.

- **RN-R020 — Estados Terminais Irreversíveis**:
  Os estados `ORDER_CREATED` e `ABANDONED` são estritamente terminais e possuem lista de transições vazia (`[]`). Nenhuma transição subsequente para outro estado é permitida a partir deles.

- **RN-R021 — Regra de Auto-transição Neutra**:
  Solicitar uma transição para o mesmo estado em que o carrinho já se encontra (`new_status == current_status`) é permitido e tratado como operação neutra (no-op).

- **RN-R022 — Congelamento do Preço Unitário no Item**:
  O preço unitário do item (`unit_price`) é capturado de `product.price` apenas no momento da adição do item (`add_item`). Na atualização de quantidade (`update_item`), o preço unitário existente no `CartItem` é preservado, sem re-sincronização com o catálogo.

---

## 5. Dados de Entrada e Assinaturas (Camada de Service)

| Método | Parâmetros | Tipos | Validações de Entrada |
|---|---|---|---|
| `get_or_create_cart` | `user_id` | `str` | Não nulo |
| `create_cart` | `user_id` | `str` | Não nulo |
| `add_item` | `user_id`<br>`product_id`<br>`quantity` | `str`<br>`str`<br>`int` | `quantity > 0`<br>`product_id` conversível para int e existente no catálogo |
| `update_item` | `user_id`<br>`product_id`<br>`quantity` | `str`<br>`str`<br>`int` | `quantity >= 0`<br>`product_id` conversível para int e item existente no carrinho |
| `remove_item` | `user_id`<br>`product_id` | `str`<br>`str` | Item deve existir no carrinho |
| `apply_coupon` | `user_id`<br>`coupon_code` | `str`<br>`str` | Carrinho não vazio; cupom existente, válido e não utilizado |
| `remove_coupon` | `user_id` | `str` | Carrinho não pode estar em checkout ou finalizado |
| `start_checkout` | `user_id` | `str` | Carrinho deve possuir itens |
| `return_to_cart` | `user_id` | `str` | Carrinho deve estar no estado `IN_CHECKOUT` |
| `confirm_order` | `user_id` | `str` | Carrinho deve estar em `IN_CHECKOUT` e possuir itens |
| `abandon_cart` | `user_id` | `str` | Transição permitida a partir de `EMPTY`, `WITH_ITEMS` ou `IN_CHECKOUT` |

---

## 6. Estados e Transições

### Tabela de Transições de Estado

| Estado Atual (`from_state`) | Próximos Estados Permitidos (`to_state`) | Gatilho / Operação |
|---|---|---|
| `EMPTY` | `WITH_ITEMS` | `add_item` (ao incluir primeiro item) |
| `EMPTY` | `ABANDONED` | `abandon_cart` |
| `WITH_ITEMS` | `EMPTY` | `remove_item` ou `update_item(quantity=0)` (ao remover último item) |
| `WITH_ITEMS` | `IN_CHECKOUT` | `start_checkout` |
| `WITH_ITEMS` | `ABANDONED` | `abandon_cart` |
| `IN_CHECKOUT` | `WITH_ITEMS` | `return_to_cart` |
| `IN_CHECKOUT` | `ORDER_CREATED` | `confirm_order` (após lock e débito de estoque) |
| `IN_CHECKOUT` | `ABANDONED` | `abandon_cart` |
| `ORDER_CREATED` | *(Nenhum - Terminal)* | N/A |
| `ABANDONED` | *(Nenhum - Terminal)* | N/A |

### Diagrama de Estados Inferido

```text
    ┌───────────────┐
    │     EMPTY     │───────────────┐
    └───────────────┘               │
       │         ▲                  │
add_item         │ remove_item      │
       ▼         │ (último item)    │
    ┌───────────────┐               │
    │  WITH_ITEMS   │───────────────┤
    └───────────────┘               │
       │         ▲                  │
start_ │         │ return_          │
check_ │         │ to_cart          │ abandon_cart
out    ▼         │                  │
    ┌───────────────┐               │
    │  IN_CHECKOUT  │───────────────┤
    └───────────────┘               │
       │                            │
confirm_order                       │
       ▼                            ▼
┌───────────────┐           ┌───────────────┐
│ ORDER_CREATED │ (Terminal)│   ABANDONED   │ (Terminal)
└───────────────┘           └───────────────┘
```

---

## 7. Tratamento de Erros e Exceções

| Exceção | Mensagem / Formato | Causa / Cenário de Disparo |
|---|---|---|
| `ValueError` | `"Quantity must be a positive integer."` | Tentativa de adicionar item com quantidade `<= 0`. |
| `ValueError` | `"Quantity must be a non-negative integer."` | Tentativa de atualizar item com quantidade `< 0`. |
| `ProductNotFoundError` | `"Product with id {product_id} not found."` | Produto não localizado no catálogo ao adicionar ou atualizar item. |
| `InsufficientStockError` | `"Insufficient stock for product {product_id}. Requested: {requested}, Available: {available}"` | Estoque inferior à quantidade solicitada (na adição, atualização ou confirmação com lock). |
| `CartItemNotFoundError` | `"Item with product id {product_id} not found in cart."` | Tentativa de atualizar ou remover produto inexistente no carrinho. |
| `CartEmptyError` | `"Cannot perform this operation on an empty cart."` / `"Cannot apply a coupon to an empty cart."` / `"Cannot start checkout with an empty cart."` / `"Cannot confirm an order with an empty cart."` | Operação restrita chamada sobre carrinho sem itens. |
| `InvalidTransitionError` | `"Invalid transition from state '{from_state}' to '{to_state}'."` | Tentativa de transição não mapeada ou modificação de itens/cupons em `ORDER_CREATED` ou `IN_CHECKOUT`. |
| `InvalidCouponError` | `"Coupon does not exist."` | Código ou ID do cupom não localizado no banco. |
| `CouponExpiredError` | `"Coupon has expired."` | Data `expires_at` do cupom é anterior à data/hora atual em UTC. |
| `CouponAlreadyUsedError` | `"Coupon has already been used by this user."` / `"Coupon has already been used."` | Usuário já possui registro de utilização do cupom (validado antes e durante o commit). |

---

## 8. Observações, Comportamentos Implícitos e Limitações

1. **Ausência de Cálculo Monetário de Totais no Backend Service**:
   O `CartService` não contém métodos para cálculo de `subtotal`, desconto proporcional/absoluto de cupom ou `total`. O modelo cliente (`frontend/js/domain/cart.js`) espera que o backend (ex.: camada de schemas/API ou properties no Model) entregue os totais pré-calculados.
2. **Identificador de Pedido Fictício no Consumo de Cupom**:
   Em `CartService.confirm_order`, a chamada para `mark_coupon_as_used` utiliza o identificador fixo literal `"some_order_id"`. A integração com um serviço de pedidos (`OrderService`) está apenas esboçada em comentário.
3. **Persistência de Preço Histórico**:
   O `CartItem.unit_price` é fixado no momento do `add_item`. Se o preço do produto sofrer alteração no catálogo enquanto o item estiver no carrinho, a atualização de quantidade (`update_item`) não reajusta o `unit_price`.
4. **Camada de Domínio do Frontend Minimalista**:
   O arquivo `frontend/js/domain/product.js` encontra-se vazio (`0 bytes`). Toda a lógica de representação e validação de produtos reside no backend.
5. **Conversão de Tipos de Identificador de Produto**:
   O `CartItem` e as assinaturas de `CartService` utilizam `product_id: str`, mas para consumo de `ProductService` o identificador é convertido explicitamente para `int(product_id)`. Se uma string não numérica for fornecida, dispara `ValueError` que é capturado e tratado como `ProductNotFoundError`.
