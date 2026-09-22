# Meu E-commerce

Este é um projeto de e-commerce didático para demonstrar uma arquitetura em camadas com Python, FastAPI, SQLAlchemy e um frontend em VanillaJS.

## Pré-requisitos

- Docker
- Docker Compose (v2+)
- Make

## Setup

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd meu-ecommerce
    ```

2.  **Suba os contêineres:**
    O comando a seguir irá construir as imagens e iniciar os serviços de backend e frontend.
    ```bash
    make up
    ```

3.  **Popule o banco de dados:**
    Execute o script de seed para adicionar produtos de exemplo ao banco de dados.
    ```bash
    make seed
    ```

## Acesso

-   **Frontend:** [http://localhost:8080](http://localhost:8080)
-   **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Comandos Úteis

-   `make up`: Constrói e sobe os contêineres em modo detached.
-   `make down`: Para e remove os contêineres e volumes.
-   `make logs`: Exibe os logs dos serviços.
-   `make test`: Executa a suíte de testes completa (unitários, integração e E2E).
-   `make format`: Formata o código do backend com Ruff e Black.
-   `make seed`: Popula o banco de dados com dados de exemplo.
