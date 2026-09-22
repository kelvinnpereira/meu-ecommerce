# Diretrizes para Agentes de IA (AGENTS.md)

Este documento contém instruções e restrições obrigatórias para agentes de IA que atuarem na implementação, manutenção e evolução deste projeto.

---

## 1. Visão Geral do Projeto

Sistema de e-commerce simplificado para fins didáticos, construído com arquitetura em camadas bem delimitadas, cobertura de testes automatizados e automação via Docker e Makefile.

---

## 2. Stack Tecnológica

*   **Backend:** Python 3.11+ / FastAPI
*   **Acesso a Dados:** SQLAlchemy 2.x
*   **Banco de Dados:** SQLite (persistido em volume no contêiner `/data/ecommerce.db`)
*   **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3 simples (sem frameworks SPA)
*   **Testes:** `pytest`, `httpx` (TestClient), `pytest-playwright`
*   **Linting e Formatação:** `ruff`, `black`
*   **Orquestração:** Docker e Docker Compose

---

## 3. Estrutura e Localização de Código

*   `backend/app/api/`: Controladores e rotas HTTP (FastAPI Routers). NENHUMA lógica de negócio ou query SQL direta deve residir aqui.
*   `backend/app/services/`: Lógica de negócio e orquestração de domínio.
*   `backend/app/repositories/`: Camada exclusiva para operações no banco via SQLAlchemy.
*   `backend/app/models/`: Classes de modelos do SQLAlchemy (tabelas do banco).
*   `backend/app/schemas/`: Modelos Pydantic para validação e serialização de dados da API.
*   `frontend/js/api/`: Módulos responsáveis pelas chamadas HTTP `fetch()`.
*   `frontend/js/views/`: Código responsável exclusivamente por renderizar elementos no DOM.
*   `backend/tests/unit/`: Testes unitários com dependências mockadas.
*   `backend/tests/integration/`: Testes de rotas da API com SQLite em memória.
*   `backend/tests/e2e/`: Testes ponta a ponta com Playwright.

---

## 4. O que o Agente DEVE Fazer

1.  **Seguir o padrão em camadas estrito:** Toda nova funcionalidade deve respeitar o fluxo `Endpoint -> Service -> Repository`.
2.  **Manter a suíte de testes íntegra:** Qualquer novo endpoint ou fluxo de negócio deve vir acompanhado de testes unitários ou de integração correspondentes.
3.  **Utilizar o Makefile:** Para executar comandos no ambiente, priorize `make test`, `make format`, `make up`, etc.
4.  **Respeitar convenções de código:**
    *   Arquivos e funções Python em `snake_case`.
    *   Classes Python em `PascalCase`.
    *   Nomes de arquivos JS em `camelCase`.
    *   Sempre executar o linter/formatter (`make format`) após modificações no código Python.

---

## 5. O que o Agente NÃO DEVE Fazer

1.  **NÃO introduzir frameworks complexos de frontend:** Não adicione React, Vue, Angular, Tailwind ou similares. O frontend deve permanecer simples e sem build step complexo.
2.  **NÃO acessar o banco diretamente nos endpoints/controllers:** Controllers devem sempre delegar para a camada de Service.
3.  **NÃO alterar o banco de dados para outro sistema (ex: PostgreSQL ou MySQL)** sem solicitação explícita do usuário. A decisão por SQLite foi tomada deliberadamente para garantir agilidade e portabilidade.
4.  **NÃO contornar os testes:** Nunca ignore falhas de testes mockando indevidamente fluxos inteiros ou desabilitando testes existentes.

---

## 6. Como Rodar e Testar Localmente

*   **Subir aplicação:**
    ```bash
    make up
    ```
*   **Rodar todos os testes:**
    ```bash
    make test
    ```
*   **Verificar e formatar código:**
    ```bash
    make format
    ```
*   **Ver logs:**
    ```bash
    make logs
    ```
*   **Derrubar contêineres:**
    ```bash
    make down
    ```
