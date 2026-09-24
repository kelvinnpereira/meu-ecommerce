# FRD — Carrinho de Compras

## 1. Visão Geral
O Carrinho de Compras é a funcionalidade central responsável por permitir aos usuários reunir produtos do catálogo, ajustar quantidades, aplicar cupons de desconto promocionais e avançar pelas etapas de checkout até a criação do pedido. Ele atua como agregador temporário de intenção de compra antes da formalização do pedido.

No contexto geral do sistema de e-commerce, o Carrinho se posiciona entre a Listagem de Produtos (catálogo) e o Processamento de Pedidos, gerenciando o ciclo de vida da compra por meio de uma máquina de estados finita e coordenando a aplicação de regras de negócio de desconto e verificação otimista de estoque.

---

## 2. Atores
- **Cliente / Comprador**: Usuário que navega pela loja, adiciona/remove produtos do carrinho, ajusta quantidades, insere códigos de cupom e inicia o checkout para confirmar o pedido.
- **Sistema (Motor de Pedidos / Estoque)**: Componente de backend que valida a disponibilidade de estoque no momento da finalização do pedido, calcula descontos, persiste estados e converte o carrinho em pedido.

---

## 3. Requisitos Funcionais

### RF-001: Inicializar Carrinho
- **Descrição**: Criar um novo carrinho de compras vazio associado ao cliente/sessão.
- **Condição de disparo**: Primeiro acesso do cliente, solicitação explícita de criação ou tentativa de adição de item sem carrinho ativo existente.
- **Resultado esperado**: Carrinho criado e persistido com identificador único, status inicial `Vazio`, lista de itens vazia e totais zerados.

### RF-002: Adicionar Item ao Carrinho
- **Descrição**: Incluir uma unidade ou quantidade de um produto específico no carrinho ativo.
- **Condição de disparo**: Cliente seleciona um produto no catálogo e clica em "Adicionar ao Carrinho" informando a quantidade desejada.
- **Resultado esperado**:
  - Se o carrinho estiver no estado `Vazio`, adiciona o item e transiciona o estado para `Com Itens`.
  - Se o produto já constar no carrinho, sua quantidade é somada à quantidade existente.
  - O subtotal do item e os totais do carrinho são recalculados.
  - A quantidade solicitada é validada contra o estoque atual do produto no catálogo.

### RF-003: Atualizar Quantidade de Item
- **Descrição**: Alterar a quantidade de um item já presente no carrinho.
- **Condição de disparo**: Cliente altera o campo numérico de quantidade de um item no carrinho.
- **Resultado esperado**:
  - Se a nova quantidade for um número inteiro maior que zero, atualiza o item e recalcula os totais.
  - Se a nova quantidade for zero, o item é removido do carrinho (disparando o comportamento de RF-004).
  - Valida a nova quantidade contra o estoque atual disponível.

### RF-004: Remover Item do Carrinho
- **Descrição**: Remover completamente uma linha de item do carrinho.
- **Condição de disparo**: Cliente clica no botão/ação de remover item.
- **Resultado esperado**:
  - Item excluído do carrinho.
  - Se for o último item restante, o carrinho transiciona para o estado `Vazio` e qualquer cupom aplicado é removido.
  - Se ainda restarem itens, permanece no estado `Com Itens` e os totais são recalculados.

### RF-005: Visualizar Carrinho
- **Descrição**: Recuperar a visualização completa e consolidada do carrinho atual.
- **Condição de disparo**: Acesso à tela de carrinho ou requisição de consulta de status do carrinho.
- **Resultado esperado**: Retorno estruturado contendo: lista de itens (com ID, nome, preço unitário, quantidade, subtotal), código do cupom aplicado (se houver), valor do desconto calculado, subtotal geral, total final e status atual do carrinho.

### RF-006: Aplicar Cupom de Desconto
- **Descrição**: Vincular um cupom promocional válido ao carrinho de compras para obter desconto.
- **Condição de disparo**: Cliente insere um código de cupom no carrinho e confirma a aplicação.
- **Resultado esperado**:
  - Validação de existência, expiração e unicidade de uso por usuário.
  - Aplicação do cálculo de desconto sobre o valor total do carrinho.
  - Associação do cupom ao carrinho e recálculo dos valores finais.

### RF-007: Remover Cupom de Desconto
- **Descrição**: Desvincular o cupom de desconto atualmente aplicado ao carrinho.
- **Condição de disparo**: Cliente solicita a remoção do cupom ou o carrinho se torna `Vazio`.
- **Resultado esperado**: Cupom desassociado do carrinho e valor total recalculado sem desconto.

### RF-008: Iniciar Checkout
- **Descrição**: Avançar o carrinho para a etapa de revisão e fechamento da compra.
- **Condição de disparo**: Cliente clica em "Finalizar Compra" ou "Ir para Checkout" estando no estado `Com Itens`.
- **Resultado esperado**: Carrinho transiciona para o estado `Em Checkout`.

### RF-009: Retornar ao Carrinho para Edição
- **Descrição**: Permitir que o cliente volte do checkout para ajustar itens no carrinho.
- **Condição de disparo**: Cliente clica em "Voltar" ou "Editar Carrinho" a partir do estado `Em Checkout`.
- **Resultado esperado**: Carrinho retorna para o estado `Com Itens`.

### RF-010: Confirmar Pedido e Decrementar Estoque (Conversão)
- **Descrição**: Converter o carrinho em um pedido de compra definitivo, validando atomicamente o estoque e consumindo o cupom.
- **Condição de disparo**: Cliente confirma o pedido no estado `Em Checkout`.
- **Resultado esperado**:
  - Verificação atômica de estoque de todos os itens do carrinho.
  - Em caso de sucesso: decremento do estoque de cada produto, registro de utilização do cupom pelo usuário, criação da entidade Pedido com status `Criado`, e transição irreversível do carrinho para `Pedido Criado`.
  - Em caso de estoque insuficiente de qualquer item: bloqueio da operação, reversão de qualquer alteração e retorno de erro descritivo mantendo o carrinho no estado `Em Checkout`.

### RF-011: Abandonar Carrinho
- **Descrição**: Marcar o carrinho como abandonado por inatividade ou desistência.
- **Condição de disparo**: Expiração por timeout de inatividade ou ação de cancelamento/abandono explícito pelo usuário (aplicável aos estados `Vazio`, `Com Itens` ou `Em Checkout`).
- **Resultado esperado**: Transição do estado do carrinho para `Abandonado`. Nenhuma reserva ou estoque é afetado.

---

## 4. Regras de Negócio

### RN-001: Limite de Cupons por Carrinho (Não Cumulativo)
É permitido aplicar no máximo 1 (um) cupom de desconto por carrinho. A aplicação de um novo cupom substitui o anterior apenas se validado com sucesso, ou exige a remoção prévia do cupom ativo.

### RN-002: Uso Único de Cupom por Usuário
Um mesmo código de cupom de desconto só pode ser utilizado 1 (uma) vez por usuário. Se o usuário já tiver concluído um pedido anterior utilizando aquele cupom, o sistema deve rejeitar nova aplicação.

### RN-003: Insensibilidade a Caixa em Códigos de Cupom
Códigos de cupom devem ser tratados de forma insensível a maiúsculas e minúsculas (*case-insensitive*). Por exemplo, `DESCONTO10`, `desconto10` e `Desconto10` representam o mesmo cupom.

### RN-004: Base de Cálculo e Limites de Desconto
O desconto do cupom incide sobre o valor total dos itens do carrinho:
- **Cupom Percentual**: `desconto = total_itens * (valor_cupom / 100)`.
- **Cupom de Valor Fixo**: `desconto = min(valor_cupom, total_itens)`.
- **Piso de Valor**: O valor total da compra após aplicação do desconto nunca poderá ser inferior a zero (`total_final = max(0, total_itens - desconto)`).

### RN-005: Validade Temporal de Cupons
Um cupom só pode ser aplicado se a data corrente for menor ou igual à sua `data_expiracao`. Cupons expirados devem ser rejeitados imediatamente.

### RN-006: Estratégia de Estoque Otimista
O sistema adota estratégia puramente otimista para controle de estoque:
- Adicionar produtos ao carrinho ou colocá-lo `Em Checkout` **NÃO** reserva estoque.
- O decremento definitivo do estoque no catálogo ocorre unicamente no instante atômico da conversão do carrinho em pedido (`Em Checkout -> Pedido Criado`).

### RN-007: Tratamento de Conflito de Estoque na Finalização
Se no momento da confirmação do pedido o estoque disponível de qualquer produto for menor que a quantidade solicitada:
- A conversão é integralmente cancelada (rollback transacional).
- Nenhum estoque é decrementado.
- Nenhum pedido é gerado.
- O carrinho permanece no estado `Em Checkout`.
- O cliente recebe mensagem de erro explícita indicando o produto em falta e o estoque restante.

### RN-008: Validação de Quantidade de Itens
A quantidade de qualquer item no carrinho deve ser um número inteiro estritamente positivo (`quantidade >= 1`).
- Na adição ou edição, o sistema valida se a quantidade informada não ultrapassa o estoque disponível naquele instante no catálogo.

### RN-009: Irreversibilidade do Estado 'Pedido Criado'
O estado `Pedido Criado` é terminal e estritamente irreversível para o carrinho. Um carrinho convertido em pedido não pode receber novos itens, ter itens removidos, ter status alterado ou ser reativado. Para uma nova compra, um novo carrinho deve ser instanciado.

---

## 5. Dados de Entrada e Validações

Todas as requisições com falha de validação devem retornar resposta padronizada com código HTTP **422 Unprocessable Entity**, detalhando campos, valores recebidos e a causa do erro.

| Operação | Campo | Tipo | Obrigatório | Regras de Validação | Origem |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Adicionar Item** | `product_id` | Integer / UUID | Sim | Deve existir no catálogo de produtos ativo. | Payload |
| | `quantity` | Integer | Sim | Inteiro `>= 1`. Não pode exceder o estoque disponível atual. | Payload |
| **Atualizar Quantidade** | `product_id` | Integer / UUID | Sim | Deve corresponder a um item já presente no carrinho. | URL / Payload |
| | `quantity` | Integer | Sim | Inteiro `>= 0`. Se `0`, dispara remoção. Se `> 0`, restrito ao estoque disponível. | Payload |
| **Remover Item** | `product_id` | Integer / UUID | Sim | Deve corresponder a um item já presente no carrinho. | URL |
| **Aplicar Cupom** | `coupon_code` | String | Sim | Alfanumérico, sem espaços, comprimento de 1 a 50 caracteres. Normalizado para maiúsculas internamente. | Payload |
| **Identificação do Usuário** | `user_id` | Integer / UUID | Sim | Identificador válido do usuário para verificação de unicidade de uso de cupom e posse do carrinho. | Header / Sessão |

---

## 6. Estados e Transições

O Carrinho de Compras implementa a máquina de estados finita especificada a seguir:

```
                +-------------------+
                |       Vazio       |<---------------+
                +-------------------+                |
                          |                          |
                adicionar |                          | remover último
                 primeiro |                          | item
                    item  v                          |
                +-------------------+                |
     +--------->|     Com Itens     |----------------+
     |          +-------------------+
     |              |           ^
     |      iniciar |           | voltar para
     |     checkout |           | editar
     |              v           |
     |          +-------------------+
     +----------|    Em Checkout    |
    voltar      +-------------------+
    para editar           |
                          | confirmar
                          | pedido
                          v
                +-------------------+
                |   Pedido Criado   | (TERMINAL / IRREVERSÍVEL)
                +-------------------+

* De qualquer estado (exceto 'Pedido Criado') -> 'Abandonado' (por timeout ou ação explícita)
```

### Matriz de Transição de Estados

| Estado Origem | Ação / Disparo | Condição / Guarda | Próximo Estado | Efeitos Colaterais |
| :--- | :--- | :--- | :--- | :--- |
| *Nenhum* | Criar Carrinho | - | `Vazio` | Instancia carrinho com lista vazia. |
| `Vazio` | Adicionar Item | Quantidade válida e em estoque | `Com Itens` | Item inserido, totais recalculados. |
| `Com Itens` | Adicionar/Atualizar Item | Quantidade válida e em estoque | `Com Itens` | Item atualizado, totais recalculados. |
| `Com Itens` | Remover Item | Restam outros itens no carrinho | `Com Itens` | Item removido, totais recalculados. |
| `Com Itens` | Remover Item | Era o último item do carrinho | `Vazio` | Item removido, cupom desvinculado, totais zerados. |
| `Com Itens` | Iniciar Checkout | Carrinho possui itens válidos | `Em Checkout` | Bloqueia edição direta sem voltar estado. |
| `Em Checkout` | Voltar para Edição | Ação explícita do usuário | `Com Itens` | Libera carrinho para adição/remoção de itens. |
| `Em Checkout` | Confirmar Pedido | Todos os itens com estoque disponível | `Pedido Criado` | Decrementa estoque, registra cupom, cria Pedido. |
| `Em Checkout` | Confirmar Pedido | Pelo menos um item sem estoque suficiente | `Em Checkout` | Transação abortada, erro 409/422 retornado. |
| `Vazio`, `Com Itens`, `Em Checkout` | Abandonar | Timeout de inatividade ou desistência | `Abandonado` | Carrinho arquivado. Não afeta estoque. |
| `Pedido Criado` | *Qualquer Ação* | - | *Não Permitido* | Rejeição imediata com erro HTTP 400/409. |

---

## 7. Edge Cases e Tratamento de Erros

| Cenário | Comportamento Esperado | Código HTTP | Mensagem de Retorno |
| :--- | :--- | :--- | :--- |
| **Estoque insuficiente no Checkout** | Compra bloqueada; nenhum estoque decrementado; pedido não gerado. | `422 Unprocessable Entity` ou `409 Conflict` | `"Estoque insuficiente para o produto '[Nome do Produto]'. Quantidade solicitada: X, disponível: Y."` |
| **Cupom inexistente** | Cupom não aplicado; carrinho inalterado. | `422 Unprocessable Entity` | `"Cupom de desconto inválido ou não encontrado."` |
| **Cupom com data expirada** | Cupom não aplicado; carrinho inalterado. | `422 Unprocessable Entity` | `"O cupom informado expirou em DD/MM/AAAA."` |
| **Cupom já utilizado pelo usuário** | Cupom não aplicado; validação contra histórico de pedidos do usuário. | `422 Unprocessable Entity` | `"Este cupom já foi utilizado em uma compra anterior."` |
| **Desconto maior que o total** | Aplicação aceita, mas total final é truncado no piso zero. | `200 OK` | Total recalculado com valor zero (não gera saldo negativo). |
| **Quantidade informada <= 0 na adição** | Rejeição imediata antes de qualquer consulta a estoque. | `422 Unprocessable Entity` | `"A quantidade deve ser um número inteiro positivo maior que zero."` |
| **Tentativa de alterar carrinho já finalizado** | Bloqueio de qualquer mutação sobre carrinho em `Pedido Criado`. | `409 Conflict` | `"Não é possível alterar um carrinho cujo pedido já foi gerado."` |
| **Produto desativado/removido do catálogo** | Erro na validação de item ao tentar adicionar ou atualizar. | `404 Not Found` | `"Produto não encontrado ou indisponível no catálogo."` |

---

## 8. Fora do Escopo

Ficam explicitamente excluídos desta versão da funcionalidade:
- **Cupons Cumulativos**: Suporte à aplicação de mais de um cupom simultâneo no mesmo carrinho.
- **Cupons por Categoria / Produto Específico**: Regras complexas de cupom aplicáveis apenas a SKUs ou categorias selecionadas.
- **Reserva Pessimista de Estoque**: Bloqueio de estoque temporário com contagem regressiva enquanto o usuário navega.
- **Backorder / Encomenda**: Conclusão de pedido com itens esgotados para entrega futura.
- **Cálculo Avançado de Frete / CEP**: Integração com APIs externas de logística e transportadoras.
- **Gateway de Pagamento Real**: Processamento direto de cartão de crédito/PIX (utiliza-se confirmação simulada/didática).

---

## 9. Premissas e Dependências

- **Módulo de Produtos**: Disponibilidade de API/Repositório para consulta de preço unitário, status ativo e quantidade em estoque em tempo real.
- **Módulo de Cupons**: Estrutura de persistência contendo `código`, `tipo` (percentual/fixo), `valor` e `data_expiracao`.
- **Identificação de Usuário**: Existência de um identificador de cliente (`user_id`) para associar o carrinho e checar a RN-002 (uso único de cupom por usuário).
- **Atomicidade Transacional**: Suporte do banco de dados relacional a transações ACID na operação de confirmação do pedido, garantindo que o decremento de estoque e a criação do pedido ocorram em bloco ou sofram rollback completo.

---

## 10. Questões em Aberto

Não há questões em aberto impeditivas para a especificação funcional. As seguintes definições técnicas de suporte serão detalhadas no próximo artefato (Feature Blueprint):
- Tempo exato de tolerância (TTL) para transição automática para o estado `Abandonado`.
- Estrutura física das tabelas no banco de dados relacional (`carrinho`, `item_carrinho`, `cupom_usuario`).
