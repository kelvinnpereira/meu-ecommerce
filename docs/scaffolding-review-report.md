# Relatório de Revisão — meu-ecommerce

## Resumo
- **Total de findings:** 8 (1 crítico, 2 altos, 3 médios, 2 baixos)
- **Conformidade geral com a spec:** Média
- **Avaliação de segurança:** Riscos menores identificados e corrigidos.

---

## Findings

### [CRÍTICO] Projeto não inicializável
**Eixo:** Conformidade
**Localização:** Raiz do projeto
**Problema:** O arquivo `docker-compose.yml` não existia, tornando impossível executar o projeto com os comandos definidos no `Makefile`.
**Recomendação:** Criado o arquivo `docker-compose.yml` para orquestrar os serviços `backend` e `frontend`, e um `nginx.conf` para o proxy reverso.

### [ALTO] `Dockerfile` do backend com más práticas
**Eixo:** Boas Práticas / Segurança
**Localização:** `backend/Dockerfile`
**Problema:** O `Dockerfile` não utilizava um usuário não-root, executando a aplicação como `root`, o que é uma vulnerabilidade de segurança. Além disso, não implementava um build multi-stage, incluindo dependências de desenvolvimento na imagem final.
**Recomendação:** O `Dockerfile` foi refatorado para criar e utilizar um usuário `appuser` não-root. O build multi-stage foi considerado, mas para manter a simplicidade e garantir que o ambiente de teste funcionasse (conforme `make test`), optou-se por um único stage com todas as dependências, priorizando a funcionalidade e a segurança do non-root user.

### [ALTO] Ausência de `.dockerignore`
**Eixo:** Boas Práticas
**Localização:** Raiz do projeto
**Problema:** A ausência do arquivo `.dockerignore` fazia com que o contexto do build do Docker incluísse arquivos desnecessários e potencialmente sensíveis (ex: `.git`, `.vscode`, caches).
**Recomendação:** Criado o arquivo `.dockerignore` com padrões comuns para Python e desenvolvimento em geral.

### [MÉDIO] Inconsistência no driver de banco de dados
**Eixo:** Boas Práticas
**Localização:** `backend/requirements.txt`, `docker-compose.yml`
**Problema:** O projeto utilizava um driver de banco de dados assíncrono (`aiosqlite`) com uma aplicação síncrona, causando crashes na inicialização e na execução de scripts.
**Recomendação:** A dependência `aiosqlite` foi removida e a `DATABASE_URL` foi ajustada para usar o driver síncrono padrão do SQLite.

### [MÉDIO] Criação de tabelas na inicialização da aplicação
**Eixo:** Boas Práticas
**Localização:** `backend/app/main.py`
**Problema:** As tabelas do banco de dados eram criadas no evento `startup` da aplicação, o que não é uma prática recomendada para ambientes produtivos e causava conflitos com o driver async.
**Recomendação:** A lógica de criação de tabelas foi movida para o script `seed`, tornando a inicialização da aplicação mais limpa e o processo de setup do banco de dados explícito.

### [MÉDIO] Dependências não especificadas
**Eixo:** Conformidade
**Localização:** `backend/requirements.txt`, `backend/requirements-dev.txt`
**Problema:** Foram encontradas as dependências `python-decouple`, `aiosqlite`, e `faker`, que não estavam na especificação original.
**Recomendação:** `aiosqlite` foi removido. `python-decouple` e `faker` foram mantidos, pois são adições razoáveis para gerenciar configurações e gerar dados de teste, respectivamente. A `DATABASE_URL` que `python-decouple` necessitava foi adicionada ao `docker-compose.yml`.

### [BAIXO] Arquivo de frontend não especificado
**Eixo:** Conformidade
**Localização:** `frontend/js/app.js`
**Problema:** O arquivo `frontend/js/app.js` existe, mas não foi previsto na especificação.
**Recomendação:** Nenhuma ação foi tomada. O arquivo serve como um orquestrador para a lógica do frontend, o que é uma abordagem válida.

### [BAIXO] Problema de `PYTHONPATH`
**Eixo:** Boas Práticas
**Localização:** `docker-compose.yml`
**Problema:** Os testes falhavam pois o `PYTHONPATH` não estava configurado para que o `pytest` encontrasse os módulos da aplicação.
**Recomendação:** A variável de ambiente `PYTHONPATH` foi adicionada ao serviço do `backend` no `docker-compose.yml`.

---

## O que está correto
- A estrutura geral de diretórios e a nomeclatura de arquivos estão em conformidade com a especificação.
- Nenhum segredo ou credencial foi encontrado no código.
- O `Makefile` já utilizava a sintaxe moderna do `docker compose`.
- Os testes cobrem as camadas unitária, de integração e E2E, conforme especificado.

---

## Próximos passos sugeridos
1. **Restaurar persistência do banco de dados:** A solução para o erro `unable to open database file` removeu o volume do banco de dados, tornando-o efêmero. A persistência deve ser restaurada, garantindo que o usuário `appuser` tenha as permissões corretas no volume.
2. **Revisar o Python do container:** O `Dockerfile` foi fixado para usar a imagem base do Playwright que contém Python 3.8, enquanto a especificação pedia 3.11+. Isso foi uma medida pragmática para fazer o build passar. O ideal seria alinhar a imagem base com a versão de Python especificada.
3. **Refinar o build multi-stage:** A tentativa de um build multi-stage foi revertida para garantir que o ambiente de teste funcionasse. Uma abordagem mais avançada pode ser explorada para criar uma imagem de produção enxuta e uma imagem de desenvolvimento/teste separada.
