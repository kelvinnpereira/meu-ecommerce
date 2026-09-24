# Comparação: FRD Original vs. FRD Reverso (Carrinho de Compras)

## 1. Visão Geral e Objetivo

Este documento apresenta uma análise comparativa aprofundada entre a especificação funcional original (**FRD Original** — `docs/carrinho/frd-carrinho.md`) e a especificação inferida por engenharia reversa a partir da implementação de código (**FRD Reverso** — `docs/carrinho/reverse-frd-carrinho.md`).

O objetivo é avaliar a conformidade do software construído em relação ao planejado, identificar divergências conceituais e arquiteturais, evidenciar melhorias técnicas introduzidas durante a implementação e mapear lacunas ou comportamentos não especificados que demandam harmonização documental ou ajustes no código.

---

## 2. Resumo Executivo da Comparação

- **Aderência Global**: **Alta no núcleo transacional e ciclo de vida**. A máquina de estados finita, as regras de estoque concorrente com verificação atômica e as restrições de cupons foram fielmente reproduzidas na camada de serviço.
- **Topologia de Estados**: **100% de correspondência**. Os 5 estados (`Vazio`/`EMPTY`, `Com Itens`/`WITH_ITEMS`, `Em Checkout`/`IN_CHECKOUT`, `Pedido Criado`/`ORDER_CREATED`, `Abandonado`/`ABANDONED`) e suas transições coincidem integralmente.
- **Divergências Arquiteturais**:
  - **Cálculo de Totais e Descontos**: O FRD original atribuiu o cálculo aritmético de subtotais e descontos (RN-004) como responsabilidade do sistema/serviço. Na implementação, a camada de serviço (`CartService`) não executa cálculos monetários, delegando a totalização para schemas/models e normalização no frontend (`Cart.totals` em `cart.js`).
  - **Conversão em Pedido Real**: O FRD estipulou a geração da entidade `Pedido` vinculada. No serviço (`CartService.confirm_order`), a chamada externa está mockada (`order_id="some_order_id"`), aguardando integração completa com `OrderService`.
- **Refinamentos Técnicos Não Previstos (Ganhos de Engenharia)**:
  - **Mitigação de Deadlock (RN-R017)**: Ordenação determinística de produtos por ID antes de obter locks exclusivos (`SELECT FOR UPDATE`).
  - **Idempotência (RN-R013, RN-R021)**: Tolerância a auto-transições de estado neutras e desvinculação de cupons em carrinhos sem cupom ativo.
  - **Congelamento Histórico de Preço (RN-R022)**: Fixação do `unit_price` na adição do item, blindando a sessão de compra contra oscilações de preço do catálogo em tempo de execução.

---

## 3. Matriz de Rastreabilidade dos Requisitos Funcionais

A tabela a seguir confronta os 11 requisitos funcionais do FRD Original com os requisitos inferidos no FRD Reverso:

| RF Original | Nome (Original) | RF Reverso | Situação | Análise Comparativa |
| :--- | :--- | :--- | :--- | :--- |
| **RF-001** | Inicializar Carrinho | **RF-R001** | **Conforme com extensão** | O FRD previa criação de carrinho vazio sob demanda. O backend implementou `create_cart` e adicionou `get_or_create_cart`, padrão idiomático que unifica busca de carrinho ativo e instanciação sob demanda. |
| **RF-002** | Adicionar Item ao Carrinho | **RF-R002** | **Conforme** | Incrementa quantidade se produto já existir, valida estoque contra o catálogo e altera estado para `WITH_ITEMS`. Apenas o recálculo explícito de totais monetários foi delegado fora do `CartService`. |
| **RF-003** | Atualizar Quantidade de Item | **RF-R003** | **Conforme** | Atualiza quantidade para valor absoluto maior que zero e desvia para remoção automática quando `quantity == 0` (RN-R003), conforme exigido. |
| **RF-004** | Remover Item do Carrinho | **RF-R004** | **Conforme** | Remove a linha do item. Se for o último item, transiciona automaticamente para `EMPTY` e remove qualquer cupom vinculado (`coupon_id = None`). |
| **RF-005** | Visualizar Carrinho | **RF-R011** | **Parcial / Delegado** | O FRD exigia retorno estruturado com nomes, subtotais e totais. Na implementação, `CartService` foca em comandos (CQS). A visualização é montada por schemas da API e normalizada no cliente (`cart.js`). Observa-se a ausência do campo de nome do produto no `CartItem` da base. |
| **RF-006** | Aplicar Cupom de Desconto | **RF-R005** | **Conforme** | Valida existência, vigência temporal e unicidade de uso por usuário via `CouponService`. Exige carrinho não vazio. Vincula `coupon_id` ao carrinho. |
| **RF-007** | Remover Cupom de Desconto | **RF-R006** | **Conforme com tolerância** | Desvincula o cupom do carrinho. A implementação adicionou comportamento idempotente caso o carrinho não possua cupom associado. |
| **RF-008** | Iniciar Checkout | **RF-R007** | **Conforme** | Transiciona o carrinho de `WITH_ITEMS` para `IN_CHECKOUT`, com validação de guarda bloqueando carrinhos sem itens. |
| **RF-009** | Retornar ao Carrinho para Edição | **RF-R008** | **Conforme** | Reverte o estado de `IN_CHECKOUT` para `WITH_ITEMS`, permitindo retomar a adição/remoção de itens e cupons. |
| **RF-010** | Confirmar Pedido e Decrementar Estoque | **RF-R009** | **Conforme com limitação** | Executa transação atômica com validação de estoque com trava pessimista (`SELECT FOR UPDATE`), rollback em falha e transição para `ORDER_CREATED`. A limitação reside no ID do pedido mockado (`some_order_id`). |
| **RF-011** | Abandonar Carrinho | **RF-R010** | **Conforme no Service** | Método `abandon_cart` implementado para transicionar `EMPTY`, `WITH_ITEMS` ou `IN_CHECKOUT` para `ABANDONED`. O gatilho por inatividade (timeout/cron) permanece dependente de infraestrutura externa. |

---

## 4. Confronto das Regras de Negócio

| Regra Original | Descrição Original | Regra Reversa Correspondente | Status de Conformidade | Divergências e Detalhes de Implementação |
| :--- | :--- | :--- | :--- | :--- |
| **RN-001** | Limite de Cupons por Carrinho (Máx 1, não cumulativo) | **RN-R008**, **RN-R009** | **Conforme** | Garantido estruturalmente pela presença de um único campo chave estrangeira `coupon_id` na entidade `Cart`. |
| **RN-002** | Uso Único de Cupom por Usuário | **RN-R012**, **RN-R019** | **Conforme** | Validado antes da aplicação via `CouponRepository.get_usage_by_user_and_coupon` e revalidado com lock e tratamento de `IntegrityError` na confirmação. |
| **RN-003** | Insensibilidade a Caixa em Códigos de Cupom | *Não explicitado no Service* | **Lacuna no Service** | O `CouponService` consulta o repositório diretamente com o código informado. A normalização para maiúsculas (`upper()`) ocorre no Schema/API ou na persistência, mas não foi isolada na regra de negócio do serviço. |
| **RN-004** | Base de Cálculo e Limites de Desconto (Percentual, Fixo, Piso Zero) | *Ausente no CartService* | **Deslocamento Arquitetural** | O FRD definiu as fórmulas no núcleo do carrinho. O código alocou essa responsabilidade em camadas externas (schemas Pydantic / getters de modelo / normalização do frontend em `cart.js`). |
| **RN-005** | Validade Temporal de Cupons (`expires_at >= now`) | **RN-R011** | **Conforme com rigor** | Implementado com verificação estrita em UTC, compatível com timestamps ingênuos (*naive*) ou conscientes de fuso horário (*timezone-aware*). |
| **RN-006** | Estratégia de Estoque Otimista durante a navegação | **RN-R005**, **RN-R018** | **Conforme** | Nenhuma reserva de estoque é criada na adição ou em checkout. O bloqueio e débito definitivo ocorrem estritamente no momento do `confirm_order`. |
| **RN-007** | Tratamento de Conflito de Estoque na Finalização (Rollback total) | **RN-R018** | **Conforme** | Bloco transacional com `db.rollback()` imediato caso qualquer item não possua saldo suficiente sob lock. Carrinho permanece em `IN_CHECKOUT`. |
| **RN-008** | Validação de Quantidade de Itens (`>= 1` na adição) | **RN-R001**, **RN-R002**, **RN-R003** | **Conforme com refinamento** | A adição exige `quantity > 0`. A atualização aceita `>= 0`, transformando `0` em remoção automática transparente. |
| **RN-009** | Irreversibilidade do Estado `Pedido Criado` | **RN-R006**, **RN-R020** | **Conforme** | `ORDER_CREATED` possui lista de transições vazia (`[]`). Quaisquer mutações (`add_item`, `update_item`, etc.) disparam `InvalidTransitionError`. |

### Regras de Negócio Adicionais Inferidas (Não Previstas no FRD Original)

A engenharia reversa identificou regras e proteções essenciais que enriqueceram o comportamento do sistema:

1. **RN-R006 — Bloqueio Operacional em Checkout**: Não apenas o carrinho finalizado é bloqueado para edição; o estado `IN_CHECKOUT` também impede inclusão, exclusão ou troca de itens e cupons, forçando o retorno formal via `return_to_cart`.
2. **RN-R007 — Validação de Pertencimento do Item**: Lança `CartItemNotFoundError` ao tentar alterar ou remover produto que não está no carrinho.
3. **RN-R009 — Restrição de Cupom em Carrinho Vazio**: Lança `CartEmptyError` caso o cliente tente aplicar cupom sem antes ter adicionado itens.
4. **RN-R013 — Remoção Idempotente de Cupom**: Chamar remoção de cupom quando nenhum cupom está ativo não gera erro, retornando o próprio carrinho de forma segura.
5. **RN-R014 e RN-R016 — Guardas Anti-Vazio no Fluxo de Compra**: Impossibilidade de avançar para checkout ou confirmar pedido se a lista de itens estiver vazia (`CartEmptyError`).
6. **RN-R017 — Ordenação Anti-Deadlock**: Ordenação determinística de produtos por `int(product_id)` antes da requisição de locks relacionais pessimistas, eliminando contenções cruzadas entre transações concorrentes.
7. **RN-R021 — Auto-Transição Neutra (No-Op)**: Tentar transicionar o carrinho para o mesmo estado em que já se encontra é tratado como operação idempotente e não falha.
8. **RN-R022 — Congelamento Histórico do Preço Unitário**: Ao adicionar um item, o `unit_price` é registrado. Na edição de quantidade, esse valor é preservado, garantindo o preço contratado na adição inicial.

---

## 5. Análise Comparativa da Máquina de Estados

### Equivalência de Nomenclaturas

| Estado no FRD Original | Estado no Código / FRD Reverso | Natureza |
| :--- | :--- | :--- |
| `Vazio` | `EMPTY` | Inicial / Transitório |
| `Com Itens` | `WITH_ITEMS` | Transitório / Operacional |
| `Em Checkout` | `IN_CHECKOUT` | Transitório / Bloqueante |
| `Pedido Criado` | `ORDER_CREATED` | Terminal / Irreversível |
| `Abandonado` | `ABANDONED` | Terminal / Irreversível |

### Matriz de Transições e Guardas

| Transição | FRD Original | Implementação (Código) | Situação |
| :--- | :---: | :---: | :--- |
| `* -> EMPTY` | Permitido | Permitido (`create_cart`) | Idêntico |
| `EMPTY -> WITH_ITEMS` | Permitido (Adicionar item) | Permitido (`add_item`) | Idêntico |
| `EMPTY -> ABANDONED` | Permitido (Timeout/Ação) | Permitido (`abandon_cart`) | Idêntico |
| `WITH_ITEMS -> EMPTY` | Permitido (Remover último) | Permitido (`remove_item` / `update_item(0)`) | Idêntico |
| `WITH_ITEMS -> IN_CHECKOUT` | Permitido (Iniciar checkout) | Permitido (`start_checkout`) | Idêntico |
| `WITH_ITEMS -> ABANDONED` | Permitido (Timeout/Ação) | Permitido (`abandon_cart`) | Idêntico |
| `IN_CHECKOUT -> WITH_ITEMS` | Permitido (Voltar/Editar) | Permitido (`return_to_cart`) | Idêntico |
| `IN_CHECKOUT -> ORDER_CREATED` | Permitido (Confirmar) | Permitido (`confirm_order`) | Idêntico |
| `IN_CHECKOUT -> ABANDONED` | Permitido (Timeout/Ação) | Permitido (`abandon_cart`) | Idêntico |
| `ORDER_CREATED -> *` | Proibido (Terminal) | Proibido (`_TRANSITIONS[ORDER_CREATED] = []`) | Idêntico |
| `ABANDONED -> *` | Proibido (Terminal) | Proibido (`_TRANSITIONS[ABANDONED] = []`) | Idêntico |
| `X -> X` (Auto-transição) | Não abordado | Permitido (No-op) | Melhoria no código |

A arquitetura de estados implementada reflete com exatidão matemática o grafo de transições planejado no FRD Original.

---

## 6. Tratamento de Erros: Códigos HTTP vs. Exceções de Domínio

O FRD original especificou os cenários de erro do ponto de vista da API REST (códigos HTTP e mensagens para o usuário), enquanto o FRD reverso registrou as exceções estruturadas lançadas na camada de negócio.

| Cenário de Erro | Especificação FRD (HTTP) | Implementação no Service (Python) | Alinhamento |
| :--- | :--- | :--- | :--- |
| **Quantidade <= 0 na adição** | `422 Unprocessable Entity` | `ValueError("Quantity must be a positive integer.")` | Compatível (convertido na camada web). |
| **Quantidade < 0 na atualização** | `422 Unprocessable Entity` | `ValueError("Quantity must be a non-negative integer.")` | Compatível. |
| **Produto inexistente no catálogo** | `404 Not Found` | `ProductNotFoundError(product_id)` | Compatível (requer mapeamento para 404 no endpoint). |
| **Estoque insuficiente (adição/edição/pedido)** | `422 Unprocessable Entity` / `409 Conflict` | `InsufficientStockError(product_id, requested, available)` | Compatível (contém os metadados requeridos pelo FRD). |
| **Item inexistente no carrinho** | Não detalhado (implícito 404) | `CartItemNotFoundError(product_id)` | Refinamento positivo. |
| **Operação em carrinho vazio** | Não detalhado (implícito 422) | `CartEmptyError` | Refinamento positivo. |
| **Transição de estado inválida** | `409 Conflict` | `InvalidTransitionError(from_state, to_state)` | Compatível. |
| **Cupom inexistente** | `422 Unprocessable Entity` | `InvalidCouponError("Coupon does not exist.")` | Compatível. |
| **Cupom com data expirada** | `422 Unprocessable Entity` | `CouponExpiredError("Coupon has expired.")` | Compatível (subclasse de `InvalidCouponError`). |
| **Cupom já utilizado pelo usuário** | `422 Unprocessable Entity` | `CouponAlreadyUsedError("Coupon has already been used...")` | Compatível (captura antes do commit e em `IntegrityError`). |

---

## 7. Discrepâncias, Lacunas e Pontos de Atenção

### 7.1. Divergências e Lacunas do Código em Relação ao FRD
1. **Desacoplamento do Cálculo Financeiro**:
   - *FRD Original*: Requisito central de calcular descontos fixos, percentuais e limites de piso zero (RN-004).
   - *Código*: O `CartService` é puramente estrutural/transacional. Ele persiste o vínculo do cupom (`cart.coupon_id`), mas não calcula nem persiste totais consolidados no modelo de carrinho.
2. **Mock no Fechamento do Pedido (`OrderService`)**:
   - *FRD Original*: Conversão formal em pedido definitivo (RF-010).
   - *Código*: Em `CartService.confirm_order`, a gravação do uso de cupom recebe `"some_order_id"` estático e a chamada `order_service.create_from_cart(cart)` está comentada como fora de escopo do serviço de carrinho.
3. **Ausência do Nome do Produto no Item (`CartItem`)**:
   - *FRD Original*: RF-005 explicita retorno contendo ID, nome do produto e preço unitário.
   - *Código*: `CartItem` armazena apenas `product_id`, `quantity` e `unit_price`. Não há join/relação direta no modelo para preencher o nome sem consulta adicional ao serviço de produtos.
4. **Mecanismo de Abandono por Timeout**:
   - *FRD Original*: RF-011 estabelece transição por timeout de inatividade.
   - *Código*: O método `abandon_cart` existe, mas não há scheduler, worker ou TTL no Redis/PostgreSQL automatizando essa transição no repositório.

### 7.2. Ganhos e Decisões de Projeto do Código sobre o FRD
1. **Concorrência e Prevenção de Deadlock**:
   - O FRD citava atomicidade ACID genérica. O código implementou mitigação de deadlocks com ordenação de chaves primárias antes de executar bloqueios de linha (`SELECT FOR UPDATE`), elevando a resiliência do sistema em alta carga.
2. **Preservação de Preço Histórico**:
   - O código adota a prática recomendada de e-commerce de fixar o preço de venda no momento em que o item é adicionado, impedindo que atualizações de quantidade sincronizem preços novos se o lojista alterou o preço do catálogo durante o fluxo do cliente.
3. **Idempotência**:
   - Auto-transições no-op e remoção tolerante de cupom garantem que retentativas de requisições de rede (*retries*) não resultem em falhas operacionais desnecessárias.

---

## 8. Conclusão e Recomendações

A comparação demonstra uma **notável consistência funcional e conceitual** entre o FRD Original e a implementação retratada no FRD Reverso. As decisões centrais de negócio — em especial o controle otimista de estoque na navegação combinado com trava pessimista na conversão, a unicidade de cupons e a máquina de estados rigorosa — foram integralmente respeitadas no código.

### Recomendações para Harmonização:

1. **Atualização da Documentação (FRD Original)**:
   - Registrar no FRD original a regra de congelamento de preço histórico (`RN-R022`).
   - Formalizar o comportamento de auto-transições neutras e idempotência na remoção de cupom.
   - Esclarecer que o cálculo financeiro de totais é derivado/projetado para visualização, e não computado pelo serviço transacional de carrinho.
2. **Ajustes de Implementação**:
   - Substituir a string fictícia `"some_order_id"` em `confirm_order` pela integração efetiva com a camada de geração de pedidos.
   - Garantir a normalização case-insensitive explícita dos códigos de cupom (`code.strip().upper()`) antes da validação.
   - Adicionar mecanismo em segundo plano (scheduler/cronjob) para processar o abandono automático de carrinhos inativos após período de tolerância definido.
