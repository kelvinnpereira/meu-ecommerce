# Blueprint de Desenvolvimento: Scaffolding E-commerce

Este documento descreve o plano de desenvolvimento para a implementação do scaffolding inicial do projeto de e-commerce, com base na `scaffolding-specification.md`. O objetivo é construir um fluxo vertical completo e testável para a **Listagem de Produtos**, garantindo que a arquitetura, as ferramentas e as convenções estejam funcionando corretamente antes de expandir para outras funcionalidades.

---

## 1. Visão Geral do Plano

**Objetivo:** Implementar o fluxo de ponta a ponta (banco de dados -> backend -> frontend) para listar produtos. Isso servirá como uma "prova de saúde" da arquitetura em camadas e validará o setup de testes (unitário, integração e E2E).

**Entidade de Exemplo:** `Produto`, conforme definido na especificação.

**O que está no escopo:**
- Configuração do ambiente com Docker Compose.
- Implementação da camada de persistência (Model, Repository) para a entidade `Produto`.
- Implementação da camada de negócio (Service) e API (Endpoint) para `Produto`.
- Desenvolvimento de uma página de frontend em Vanilla JS para buscar e exibir os produtos.
- Criação de um script `seed` para popular o banco com dados de exemplo.
- Implementação de testes unitários, de integração e E2E para o fluxo de listagem.

**O que NÃO está no escopo:**
- Funcionalidades de carrinho de compras, checkout, ou autenticação de usuários.
- Interface de administração de produtos (CRUD completo).
- Paginação ou filtros na listagem de produtos.

**Critérios de Sucesso:**
1. O comando `make up` sobe os contêineres do backend e frontend sem erros.
2. O comando `make seed` popula o banco de dados com pelo menos 3 produtos de exemplo.
3. Acessar `http://localhost:<frontend_port>` no navegador exibe a lista de produtos populada pelo seed.
4. O comando `make test` executa com sucesso, com todos os testes (unitários, integração e E2E) passando.
5. O comando `make format` executa e formata o código sem erros.

---

## 2. Implementação da Entidade de Exemplo (`Produto`)

As etapas seguirão a ordem "de dentro para fora": do banco de dados para a interface.

### Etapa 2.1: Backend - Camada de Persistência
- **O que fazer:** Definir a estrutura da tabela `products` e o contrato para acessá-la.
- **Onde:**
    - `backend/app/models/product.py`: Modelo ORM do SQLAlchemy.
    - `backend/app/schemas/product.py`: Schema Pydantic para validação e serialização de dados.
    - `backend/app/repositories/product_repository.py`: Classe que interage com o banco de dados usando SQLAlchemy.
- **Como:**
    - Em `models/product.py`, criar a classe `Product` que mapeia para a tabela `products` com os campos `id`, `name`, `description`, `price`, `stock`.
    - Em `schemas/product.py`, criar o schema `Product` Pydantic para representar os dados que serão expostos pela API.
    - Em `repositories/product_repository.py`, criar a classe `ProductRepository` com um método `list_all()` que executa uma query `SELECT` em todos os produtos.
- **Resultado esperado:** A estrutura de dados do produto está definida e há uma classe capaz de buscar todos os produtos no banco de dados.

### Etapa 2.2: Backend - Camada de Negócio e API
- **O que fazer:** Expor os dados dos produtos através de um endpoint HTTP.
- **Onde:**
    - `backend/app/services/product_service.py`: Lógica de negócio.
    - `backend/app/api/v1/endpoints/products.py`: Endpoint da API.
    - `backend/app/main.py`: Registro da rota da API.
- **Como:**
    - Em `services/product_service.py`, criar a classe `ProductService` que utiliza o `ProductRepository` para buscar os produtos. Inicialmente, o serviço será um simples repassador.
    - Em `endpoints/products.py`, criar um router FastAPI e a rota `GET /api/v1/products` que usa o `ProductService` para obter a lista de produtos e a retorna.
    - Em `main.py`, registrar o router de produtos na instância principal do FastAPI.
- **Resultado esperado:** Acessar `http://localhost:<backend_port>/api/v1/products` retorna um JSON com a lista de produtos do banco.

### Etapa 2.3: Frontend - Camada de Apresentação
- **O que fazer:** Criar a interface para buscar e renderizar a lista de produtos.
- **Onde:**
    - `frontend/index.html`: Estrutura da página.
    - `frontend/js/api/productsApi.js`: Módulo de comunicação com a API.
    - `frontend/js/views/productView.js`: Módulo de manipulação do DOM.
- **Como:**
    - Em `index.html`, criar a estrutura básica com um `<div id="products-container">`.
    - Em `productsApi.js`, criar a função `fetchProducts()` que usa `fetch()` para chamar o endpoint `GET /api/v1/products`.
    - Em `productView.js`, criar a função `renderProducts(products)` que recebe a lista de produtos, itera sobre ela e injeta o HTML correspondente (cards de produto) no `products-container`.
    - Adicionar um script principal que chama `fetchProducts()` e passa o resultado para `renderProducts()` no carregamento da página.
- **Resultado esperado:** Abrir `index.html` em um navegador dispara a chamada à API e exibe os produtos na tela.

---

## 3. Plano de Seed

- **O que gerar:** De 3 a 5 registros da entidade `Produto` com nomes, descrições e preços variados para garantir que a listagem funcione visualmente.
- **Onde:** `backend/app/scripts/seed.py`.
- **Como executar:** Através do comando `make seed`, que irá invocar `docker-compose exec backend python -m app.scripts.seed`.
- **Como implementar:**
    - O script `seed.py` obterá uma sessão do banco de dados (usando `SessionLocal` de `app.database`).
    - Ele verificará se já existem produtos no banco. Se não houver, criará uma lista de objetos do modelo `Product` e os adicionará à sessão.
    - Ao final, comitará a transação e fechará a sessão.
- **Dados representativos:**
    ```python
    [
        Product(name="Laptop Moderno", description="Processador i7, 16GB RAM, SSD 512GB", price=4500.00, stock=15),
        Product(name="Mouse Sem Fio Ergonômico", description="Conexão Bluetooth e 2.4GHz", price=150.75, stock=50),
        Product(name="Teclado Mecânico RGB", description="Switches Blue, layout ABNT2", price=350.00, stock=30),
    ]
    ```

---

## 4. Plano de Testes

### Etapa 4.1: Configuração do Ambiente de Teste
- **O que fazer:** Configurar o `pytest` e as fixtures necessárias.
- **Onde:** `backend/tests/conftest.py`.
- **Como:** Criar uma fixture que fornece um `TestClient` para a aplicação FastAPI e outra que gerencia um banco de dados SQLite em memória para isolar os testes.

### Etapa 4.2: Testes Unitários
- **O que testar:** A lógica de `ProductService`, garantindo que ele chame corretamente o repositório.
- **Onde:** `backend/tests/unit/test_product_service.py`.
- **Como:** Criar um teste que instancia `ProductService` com um `ProductRepository` "mockado" (usando `unittest.mock.MagicMock`). Chamar o método de listagem do serviço e verificar se o método correspondente do repositório foi chamado uma vez.

### Etapa 4.3: Testes de Integração de API
- **O que testar:** O endpoint `GET /api/v1/products` de forma integrada.
- **Onde:** `backend/tests/integration/test_products_endpoint.py`.
- **Como:** Usar a fixture `TestClient`. O teste fará uma requisição `GET` para `/api/v1/products`, verificará se o status code da resposta é 200 e se o corpo da resposta é uma lista JSON válida. O banco de dados em memória será populado antes da requisição para validar o conteúdo.

### Etapa 4.4: Testes E2E de Frontend
- **O que testar:** O fluxo completo do usuário: abrir a página e ver a lista de produtos renderizada.
- **Onde:** `backend/tests/e2e/test_product_listing_ui.py`.
- **Como:** Usar `pytest-playwright`. O teste irá:
    1. Iniciar a aplicação completa via Docker Compose.
    2. Navegar para a página `index.html`.
    3. Aguardar que os elementos correspondentes aos produtos (ex: cards com o nome dos produtos) apareçam na tela.
    4. Afirmar que os nomes dos produtos semeados no banco de dados estão visíveis no DOM.

---

## 5. Sequência de Implementação

1.  **[Infra]** Criar `docker-compose.yml`, `backend/Dockerfile`, e `Makefile` inicial.
2.  **[Infra]** Configurar `backend/app/database.py` e `backend/app/main.py` básicos.
3.  **[Backend]** Implementar `backend/app/models/product.py`.
4.  **[Backend]** Implementar `backend/app/schemas/product.py`.
5.  **[Backend]** Implementar `backend/app/repositories/product_repository.py`.
6.  **[Backend]** Implementar `backend/app/services/product_service.py`.
7.  **[Backend]** Implementar `backend/app/api/v1/endpoints/products.py` e registrar a rota.
8.  **[Teste]** Implementar o teste unitário em `tests/unit/test_product_service.py`.
9.  **[Teste]** Implementar o teste de integração em `tests/integration/test_products_endpoint.py`.
10. **[Seed]** Implementar o script `backend/app/scripts/seed.py`.
11. **[Infra]** Executar `make up` e `make seed` para validar o backend e a persistência.
12. **[Frontend]** Desenvolver `frontend/index.html` e os estilos CSS.
13. **[Frontend]** Implementar `frontend/js/api/productsApi.js`.
14. **[Frontend]** Implementar `frontend/js/views/productView.js` e o script principal de orquestração.
1V. **[Teste]** Implementar o teste E2E em `tests/e2e/test_product_listing_ui.py`.
16. **[Final]** Executar o ciclo completo: `make format`, `make test`, `make down`, `make up` para garantir que tudo está funcionando de forma integrada.

---

## 6. Pontos de Atenção

- **Configuração do Playwright no Docker:** O `Dockerfile` do backend precisa instalar corretamente o `playwright` e suas dependências de navegador (`playwright install chromium`), o que pode aumentar o tamanho da imagem.
- **CORS (Cross-Origin Resource Sharing):** O backend FastAPI precisará ser configurado com o `CORSMiddleware` para permitir que o frontend (servido de uma origem diferente, mesmo que seja `localhost` em outra porta) faça requisições à API.
- **Dependência entre Testes E2E e o Seed:** Os testes E2E dependerão que os dados do `seed` sejam conhecidos e estáveis para fazer as asserções corretas na interface. A estratégia de teste deve garantir que o banco esteja em um estado conhecido antes de cada execução de teste E2E.
- **Portas de Serviço:** O `docker-compose.yml` deve mapear as portas do backend e do frontend de forma clara para evitar conflitos na máquina host.

---

Este plano está alinhado com o que você espera? Há algo que quer ajustar, adicionar ou remover antes de começarmos a implementação?
