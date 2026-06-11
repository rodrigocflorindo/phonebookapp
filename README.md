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
|-- k8s/
|   `-- phonebookapp.yaml
|-- app.py
|-- compose.yaml
|-- Dockerfile
`-- README.md
```

## Executar no Kubernetes do GIRUS

O manifesto cria um namespace próprio, um Deployment, um Service e um volume
persistente de 1 GiB para o SQLite.

Confirme que o contexto ativo é o cluster GIRUS:

```bash
kubectl config use-context kind-girus
```

Construa a imagem e carregue-a no nó do Kind:

```bash
docker build -t phonebookapp:1.0.0 .
kind load docker-image phonebookapp:1.0.0 --name girus
```

Aplique todos os recursos:

```bash
kubectl apply -f k8s/phonebookapp.yaml
kubectl rollout status deployment/phonebookapp -n phonebook-app
```

Publique o serviço localmente:

```bash
kubectl port-forward -n phonebook-app service/phonebookapp 3001:3000
```

Acesse [http://localhost:3001](http://localhost:3001).

Verifique os recursos:

```bash
kubectl get all,pvc -n phonebook-app
```

Remova a aplicação e o banco:

```bash
kubectl delete -f k8s/phonebookapp.yaml
```

> O Deployment usa uma única réplica porque o SQLite armazena os dados em um
> único arquivo. Para escalar horizontalmente, substitua o SQLite por um banco
> como PostgreSQL.

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
