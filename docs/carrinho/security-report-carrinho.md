# Relatório de Segurança (Red Team) — Funcionalidade de Carrinho e Cupons

## Resumo
- **Total de findings**: 7 (1 Crítico, 2 Altos, 3 Médios, 1 Baixo)
- **Corrigidos nesta sessão**: 6 (SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07)
- **Pendentes / Aceitos por Escopo**: 1 (SEC-01 — Crítico: controle de acesso e IDOR/BOLA via `X-User-ID`, aceito por delimitação de escopo com mitigação parcial de formato)
- **Status dos testes**: 124/124 testes aprovados (incluindo testes de segurança, unitários, integração e E2E)

---

## Findings

### 1. [CRÍTICO] SEC-01: Controle de Acesso Quebrado e Risco de IDOR/BOLA via `X-User-ID`
- **Categoria OWASP**: A01:2021 – Broken Access Control (CWE-639 / CWE-284)
- **Localização**: `backend/app/api/deps.py:22-31`
- **Status**: **Pendente / Aceito por Escopo** (Risco aceito por delimitação do escopo do projeto; mitigação parcial de sanitização/formato de entrada aplicada)
- **Vetor de ataque que continua aberto**:
  - A validação introduzida no cabeçalho `X-User-ID` confere exclusivamente a sintaxe e o formato do valor recebido (restringindo a até 64 caracteres alfanuméricos, hífen ou underline via regex `^[a-zA-Z0-9_\-]{1,64}$`, além de rejeitar strings vazias/espaços com HTTP 400).
  - **O vetor de usurpação de identidade continua totalmente aberto**: qualquer cliente ou atacante pode inspecionar, mutar, esvaziar, aplicar cupons ou finalizar o pedido no carrinho de compras de qualquer outro usuário simplesmente alterando o valor do cabeçalho `X-User-ID` na requisição (por exemplo, alternando de `user-1` para `user-2`).
  - Não há verificação criptográfica de identidade, assinatura digital, token de sessão ou mecanismo de autenticação/autorização no backend que vincule a requisição à real identidade do emissor.
- **Justificativa do Aceite de Risco por Escopo**:
  - Mecanismos de autenticação e gestão de identidade de usuários (como JWT, OAuth2, sessões seguras com cookies ou OIDC) foram deliberadamente definidos como fora do escopo deste exercício.
  - Para manter a fidelidade técnica irrestrita do relatório de segurança, a vulnerabilidade não é dada como resolvida, mas sim reclassificada como **Pendente** e formalmente **Aceita por Escopo**.
- **Mitigação Parcial Aplicada (Camada de Entrada/Sintaxe)**:
  - Sanitização de espaços em branco e validação estrita de formato em `deps.get_user_id`.
  - Rejeição de strings vazias, caracteres especiais fora do padrão e identificadores com mais de 64 caracteres com HTTP 400 (mitigando injeções pontuais e overflow na camada de transporte).
- **Recomendação de Autenticação (Obrigatória para Produção)**:
  - Eliminar a confiança cega no cabeçalho HTTP não autenticado `X-User-ID`.
  - Adotar autenticação robusta padrão de mercado (ex.: OAuth 2.0 / OpenID Connect com tokens JWT assinados assimetricamente ou sessões com cookies `HttpOnly`/`Secure`).
  - O identificador do usuário (`user_id` / `sub`) deve ser extraído e validado no servidor exclusivamente a partir das credenciais criptografadas verificadas, impedindo completamente o vetor de IDOR/BOLA.

---

### 2. [ALTO] SEC-02: Bypass de Expiração de Cupom na Confirmação de Pedido (TOCTOU)
- **Categoria OWASP**: A04:2021 – Insecure Design / Flaw in Business Logic (CWE-367)
- **Localização**: `backend/app/services/cart_service.py:307`, `backend/app/services/coupon_service.py:65`
- **Vetor de ataque**: Um usuário aplicava um cupom antes de expirar e aguardava dias antes de confirmar o pedido. O endpoint de confirmação executava apenas a gravação de uso sem revalidar a data de expiração, aplicando desconto inválido.
- **Status**: Corrigido
- **Correção aplicada**:
  - `CouponService.mark_coupon_as_used` agora chama `validate_coupon_by_id`, revalidando data de expiração (`expires_at < now`) e uso prévio imediatamente antes da gravação do uso dentro da transação atômica de `confirm_order`.

---

### 3. [ALTO] SEC-03: Race Condition no Uso Único de Cupom Promocional
- **Categoria OWASP**: A04:2021 – Insecure Design / Concurrency (CWE-362)
- **Localização**: `backend/app/models/coupon.py:28`, `backend/app/services/cart_service.py:321`
- **Vetor de ataque**: Requisições simultâneas de checkout disparadas em paralelo para o mesmo usuário e cupom passavam pela checagem de uso antes do primeiro commit, permitindo que o mesmo cupom de uso único fosse utilizado em múltiplos pedidos.
- **Status**: Corrigido
- **Correção aplicada**:
  - Adicionada restrição de unicidade no banco de dados: `UniqueConstraint("user_id", "coupon_id", name="uq_user_coupon_usage")` no modelo `UserCouponUsage`.
  - Tratamento de `IntegrityError` adicionado em `CartService.confirm_order` com rollback automático e lançamento de `CouponAlreadyUsedError` (HTTP 422).

---

### 4. [MÉDIO] SEC-04: Vulnerabilidade a Cross-Site Scripting (XSS) via Interpolação no DOM
- **Categoria OWASP**: A03:2021 – Injection (XSS - CWE-79)
- **Localização**: `frontend/js/views/cartView.js:37-58`, `frontend/js/views/productView.js:14-25`
- **Vetor de ataque**: Produtos cadastrados com caracteres HTML ou atributos maliciosos em campos como `name`, `id` ou `image_url` executavam scripts arbitrários no navegador do usuário ao serem inseridos via `innerHTML`.
- **Status**: Corrigido
- **Correção aplicada**:
  - Criado o módulo `frontend/js/utils/sanitize.js` contendo as funções `escapeHtml` e `sanitizeUrl`.
  - Atualizadas as funções de renderização `renderCartItem` e `renderProducts` para escapar todas as propriedades dinâmicas e filtrar esquemas de URL perigosos (como `javascript:` ou `data:`).

---

### 5. [MÉDIO] SEC-05: Falta de Limites em Campos de Entrada Numéricos e Textuais (Resource Exhaustion / DoS)
- **Categoria OWASP**: A04:2021 – Insecure Design / Input Validation (CWE-20, CWE-1284)
- **Localização**: `backend/app/schemas/cart.py:18-30`, `backend/app/schemas/coupon.py:20-30`
- **Vetor de ataque**: Submissão de quantidades astronômicas (`quantity > 10^18`) ou códigos de cupom e `product_id` arbitrariamente extensos para causar overflow no tipo `Numeric(10, 2)` do banco ou exaustão de memória/processamento.
- **Status**: Corrigido
- **Correção aplicada**:
  - Restrição de `quantity` para limite plausível (`gt=0, le=9999`) em `CartItemCreate` e (`ge=0, le=9999`) em `CartItemUpdate`.
  - Restrição estrita de `product_id` para identificador numérico via regex `pattern=r"^\d+$"` e `max_length=20`.
  - Restrição de tamanho máximo de 50 caracteres para `coupon_code` com validação de preenchimento obrigatório após remoção de espaços.

---

### 6. [MÉDIO] SEC-06: Ausência de Headers de Segurança HTTP e Content-Security-Policy (CSP)
- **Categoria OWASP**: A05:2021 – Security Misconfiguration (CWE-16)
- **Localização**: `backend/app/main.py:15`, `frontend/index.html:5`
- **Vetor de ataque**: Exposição a Clickjacking (aplicação embutida em iframes), sniffing de MIME type pelo navegador e execução de scripts de terceiros.
- **Status**: Corrigido
- **Correção aplicada**:
  - Middleware em `backend/app/main.py` injetando:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Referrer-Policy: strict-origin-when-cross-origin`
    - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
  - Meta tag `Content-Security-Policy` adicionada no `frontend/index.html` restringindo origens de scripts, estilos, conexões e imagens.

---

### 7. [BAIXO] SEC-07: Falta de Rollback Explícito no Gerenciador de Sessão (`get_db`)
- **Categoria OWASP**: A05:2021 – Security Misconfiguration / Robustness (CWE-703)
- **Localização**: `backend/app/api/deps.py:11-18`
- **Vetor de ataque**: Em caso de falha não tratada em rota com sessão aberta e transação não finalizada, a conexão retornava com estado inconsistente para o pool.
- **Status**: Corrigido
- **Correção aplicada**: Adicionado bloco `except Exception: db.rollback(); raise` antes do `finally: db.close()` no gerador `get_db`.

---

## Testes de Segurança Adicionados

Arquivo criado: `backend/tests/integration/test_security.py`

1. `test_security_headers_present`: Valida a injeção obrigatória dos headers `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Permissions-Policy`.
2. `test_user_id_validation_invalid_characters`: Valida que caracteres maliciosos ou inválidos no cabeçalho `X-User-ID` retornam HTTP 400.
3. `test_user_id_validation_excessive_length`: Valida rejeição com HTTP 400 de `X-User-ID` com mais de 64 caracteres.
4. `test_user_id_whitespace_only`: Valida rejeição de cabeçalho `X-User-ID` preenchido apenas com espaços em branco.
5. `test_add_item_quantity_upper_bound`: Garante que quantidades abusivas (`quantity > 9999`) retornam HTTP 422.
6. `test_add_item_non_numeric_product_id`: Garante que `product_id` não-numérico é rejeitado com HTTP 422.
7. `test_coupon_code_length_limit`: Garante que código de cupom com mais de 50 caracteres retorna HTTP 422.
8. `test_coupon_expiration_revalidated_at_confirm_order`: Comprova que um cupom expirado após inserção no carrinho é bloqueado durante o `confirm_order` com HTTP 422 e não gera o pedido.
9. `test_user_coupon_usage_unique_constraint`: Comprova que a restrição de unicidade no banco de dados bloqueia tentativas concorrentes de reuso do mesmo cupom pelo mesmo usuário via `IntegrityError`.

---

## Recomendações Pendentes e Próximos Passos (Roadmap)
- **Autenticação Centralizada (SEC-01 — PENDENTE / ACEITO POR ESCOPO)**:
  - **Vetor aberto**: Usurpação direta de identidade e manipulação de carrinhos de terceiros (IDOR/BOLA) via alteração manual do cabeçalho `X-User-ID`.
  - **Recomendação**: Implementar autenticação baseada em tokens assinados (OAuth2 / OIDC com JWT) ou sessões gerenciadas pelo servidor. O backend deve derivar a identidade do usuário a partir do token verificado, eliminando o cabeçalho não autenticado `X-User-ID`.
- **Rate Limiting**: Implementar limitação de taxa (ex: `slowapi` ou Redis token bucket) nas rotas de aplicação de cupom (`/cart/coupon`) e confirmação (`/cart/confirm`) para mitigar tentativas de força bruta e DoS.
