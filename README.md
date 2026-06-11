# Phonebook App

Agenda web simples para cadastrar, pesquisar, editar e excluir contatos.

![Tela do Phonebook App](docs/phonebook-app.png)

## Funcionalidades

- Cadastro de nome e telefone
- Pesquisa instantânea de contatos
- Edição e exclusão de registros
- Validação dos dados no frontend e backend
- Persistência em banco SQLite
- Interface responsiva
- Execução isolada com Docker

## Tecnologias

- **Frontend:** HTML, CSS e JavaScript
- **Backend:** Python 3.12
- **Banco de dados:** SQLite
- **Infraestrutura local:** Docker Compose

## Arquitetura

O backend Python serve os arquivos estáticos e disponibiliza uma API REST. Os
contatos são armazenados em um banco SQLite dentro de um volume Docker.

```text
Navegador
   |
   | HTTP :3001
   v
Aplicação Python
   |-- Frontend estático
   |-- API REST /api/contacts
   |
   v
SQLite /data/contacts.db
```

## Pré-requisitos

- Docker Desktop
- Docker Compose

## Executar

Clone o repositório:

```bash
git clone https://github.com/rodrigocflorindo/phonebookapp.git
cd phonebookapp
```

Construa e inicie o container:

```bash
docker compose up -d --build
```

Em instalações que usam o executável clássico:

```bash
docker-compose up -d --build
```

Acesse [http://localhost:3001](http://localhost:3001).

## Parar

```bash
docker compose down
```

Para remover também o banco de dados:

```bash
docker compose down -v
```

## Persistência

O volume `phonebook-data` armazena o arquivo `/data/contacts.db`. Os contatos
permanecem disponíveis após reiniciar ou recriar o container.

## API

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/api/health` | Verifica a saúde da aplicação |
| `GET` | `/api/contacts` | Lista os contatos |
| `POST` | `/api/contacts` | Cria um contato |
| `PUT` | `/api/contacts/{id}` | Atualiza um contato |
| `DELETE` | `/api/contacts/{id}` | Exclui um contato |

Consulte os exemplos em [docs/API.md](docs/API.md).

## Estrutura

```text
phonebookapp/
|-- static/
|   |-- app.js
|   |-- index.html
|   `-- styles.css
|-- docs/
|   |-- API.md
|   `-- phonebook-app.png
|-- app.py
|-- compose.yaml
|-- Dockerfile
`-- README.md
```

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
