# Phonebook App

Aplicação web moderna para gerenciamento de contatos com interface responsiva, validação robusta e observabilidade integrada com Prometheus e Grafana.

![Tela do Phonebook App](docs/phonebook-app.png)

## Funcionalidades

### Gerenciamento de Contatos
- ✅ **Cadastro** de nome e telefone com validação em tempo real
- 🔍 **Pesquisa instantânea** filtrando por nome ou telefone
- ✏️ **Edição inline** de contatos existentes
- 🗑️ **Exclusão** com confirmação
- 📊 **Contador dinâmico** exibindo total de contatos cadastrados

### Interface e Experiência
- 📱 **Design responsivo** adaptado para desktop, tablet e mobile
- 🎨 **Animações suaves** em todas as interações
- ♿ **Acessibilidade** com ARIA labels e navegação por teclado
- 🌙 **Avatar colorido** gerado automaticamente para cada contato
- 💬 **Sistema de feedback** com modal para sugestões dos usuários
- ⚡ **Estado vazio** explicativo quando não há contatos

### Validação e Segurança
- ✔️ **Validação dupla**: frontend (JavaScript) e backend (Python)
- 📏 **Nome**: 2-80 caracteres, trimming automático de espaços
- 📞 **Telefone**: 8-20 caracteres, aceita números, espaços e símbolos `()+-`
- 📧 **Feedback**: email opcional, mensagem de 10-500 caracteres

### Observabilidade
- 📈 **Prometheus** para coleta de métricas
- 📊 **Grafana** para visualização com dashboards pré-configurados
- 🔍 **Métricas detalhadas** de requisições HTTP, latência e operações de banco de dados
- ⚕️ **Health check** e endpoint `/metrics` para monitoramento
- 📊 **Dashboards**: Phonebook App Metrics e Kubernetes Cluster Health

## Tecnologias

- **Frontend:** HTML5, CSS3 (Grid, Flexbox, Animations), Vanilla JavaScript (ES6+)
- **Backend:** Python 3.12 com `http.server` e threading
- **Banco de dados:** SQLite 3 com row factory
- **Observabilidade:** Prometheus + Grafana
- **Infraestrutura:** Docker, Docker Compose, Kubernetes (Kind)

## Arquitetura

A aplicação usa uma arquitetura simples e eficiente com backend Python servindo tanto arquivos estáticos quanto API REST. As métricas são expostas no formato Prometheus para monitoramento.

```text
┌─────────────────────────────────────────────────────────┐
│                      Navegador                          │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   HTML5    │  │  JavaScript  │  │   CSS3/Grid   │  │
│  └────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP :3001
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Aplicação Python (ThreadingHTTPServer)        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Prometheus Metrics Instrumentation              │  │
│  │  ├── HTTP request counter & duration histogram   │  │
│  │  ├── In-progress requests gauge                  │  │
│  │  └── Database operations counter                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────┐  ┌──────────────────────────────┐  │
│  │ Static Files  │  │    API REST                   │  │
│  │ - index.html  │  │ GET    /api/health           │  │
│  │ - app.js      │  │ GET    /api/contacts         │  │
│  │ - styles.css  │  │ POST   /api/contacts         │  │
│  └───────────────┘  │ PUT    /api/contacts/{id}    │  │
│                     │ DELETE /api/contacts/{id}    │  │
│                     │ POST   /api/feedback         │  │
│                     │ GET    /metrics (Prometheus) │  │
│                     └──────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite Database (Volume)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  contacts table                                   │  │
│  │  ├── id (INTEGER PRIMARY KEY AUTOINCREMENT)      │  │
│  │  ├── name (TEXT NOT NULL)                        │  │
│  │  ├── phone (TEXT NOT NULL)                       │  │
│  │  └── created_at (TEXT DEFAULT CURRENT_TIMESTAMP) │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  feedback table                                   │  │
│  │  ├── id (INTEGER PRIMARY KEY AUTOINCREMENT)      │  │
│  │  ├── email (TEXT, nullable)                      │  │
│  │  ├── message (TEXT NOT NULL)                     │  │
│  │  └── created_at (TEXT DEFAULT CURRENT_TIMESTAMP) │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Prometheus + Grafana                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Prometheus: coleta métricas a cada 15s          │  │
│  │ Grafana: dashboards de visualização             │  │
│  │ - Phonebook App Metrics                         │  │
│  │ - Kubernetes Cluster Health                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Decisões Arquiteturais

- **Single-threaded HTTP server com threading**: usa `ThreadingHTTPServer` para lidar com múltiplas requisições concorrentes
- **Decorator pattern para métricas**: `@traced_request` instrumenta requisições sem poluir a lógica de negócio
- **Health check e metrics exclusion**: `/api/health` e `/metrics` não geram métricas detalhadas para evitar ruído
- **Resource naming normalizado**: IDs dinâmicos são substituídos por `{id}` para agrupamento de métricas
- **SQLite com row factory**: retorna dicionários em vez de tuplas para fácil serialização JSON

## Pré-requisitos

- Docker Desktop
- Docker Compose (ou Kind para Kubernetes)

## Executar Localmente

Clone o repositório:

```bash
git clone https://github.com/rodrigocflorindo/phonebookapp.git
cd phonebookapp
```

Construa e inicie o container:

```bash
docker compose up -d --build
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

## API REST

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/api/health` | Verifica a saúde da aplicação |
| `GET` | `/api/contacts` | Lista todos os contatos ordenados por nome |
| `POST` | `/api/contacts` | Cria um novo contato |
| `PUT` | `/api/contacts/{id}` | Atualiza um contato existente |
| `DELETE` | `/api/contacts/{id}` | Exclui um contato |
| `POST` | `/api/feedback` | Envia feedback sobre a aplicação |
| `GET` | `/metrics` | Expõe métricas no formato Prometheus |

### Validação de Dados

**Contatos (POST/PUT /api/contacts)**:
- `name`: string, 2-80 caracteres, obrigatório
- `phone`: string, 8-20 caracteres, padrão `^[0-9()+\-\s]{8,20}$`, obrigatório

**Feedback (POST /api/feedback)**:
- `email`: string, 0-100 caracteres, opcional, deve conter `@` se preenchido
- `message`: string, 10-500 caracteres, obrigatório

Erros de validação retornam **HTTP 400** com JSON `{"error": "mensagem"}`.

Consulte exemplos de uso em [docs/API.md](docs/API.md).

## Estrutura do Projeto

```text
phonebookapp/
├── app.py                       # Servidor HTTP Python com API REST e métricas
├── requirements.txt             # Dependências Python (prometheus-client)
├── test_app.py                  # Suite de testes unitários
├── Dockerfile                   # Build multi-stage otimizado
├── compose.yaml                 # Docker Compose com volume persistente
├── CLAUDE.md                    # Documentação para Claude Code
├── README.md                    # Este arquivo
├── static/                      # Frontend estático
│   ├── index.html              # Interface HTML5 semântica
│   ├── app.js                  # Lógica JavaScript (fetch API, DOM manipulation)
│   └── styles.css              # Estilos responsivos com Grid/Flexbox
├── docs/                        # Documentação adicional
│   ├── API.md                  # Exemplos de uso da API REST
│   └── phonebook-app.png       # Screenshot da aplicação
└── k8s/                         # Manifests Kubernetes
    ├── phonebookapp.yaml       # Namespace, PVC, Deployment, Service
    └── monitoring/              # Stack de monitoramento
        ├── prometheus.yaml     # Prometheus server
        ├── grafana.yaml        # Grafana server
        ├── grafana-dashboards.yaml  # Dashboards pré-configurados
        ├── kube-state-metrics.yaml  # Métricas do cluster K8s
        └── node-exporter.yaml  # Métricas dos nodes
```

## Testes

A aplicação inclui uma suite de testes unitários cobrindo todos os endpoints da API:

```bash
python3 -m unittest test_app.py -v
```

### Cobertura de Testes

- ✅ **CRUD de Contatos**: criar, listar, atualizar, excluir
- ✅ **Validação**: nome/telefone inválidos, campos faltando
- ✅ **Feedback**: com/sem email, validação de mensagem
- ✅ **Health check**: resposta 200 OK
- ✅ **Persistência**: dados sobrevivem entre requisições

Todos os testes usam um banco SQLite em memória para isolamento.

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `PORT` | Porta do servidor HTTP | `3000` |
| `DATABASE_PATH` | Caminho do arquivo SQLite | `data/contacts.db` |

## Executar no Kubernetes (Kind)

O manifesto cria um namespace próprio, um Deployment, um Service e um volume
persistente de 1 GiB para o SQLite.

### Pré-requisitos

- [Kind](https://kind.sigs.k8s.io/) instalado
- Cluster Kind chamado `girus`

### Deploy da Aplicação

Confirme que o contexto ativo é o cluster GIRUS:

```bash
kubectl config use-context kind-girus
```

Construa a imagem e carregue-a no nó do Kind:

```bash
docker build -t phonebookapp:1.3.0 .
kind load docker-image phonebookapp:1.3.0 --name girus
```

Aplique todos os recursos:

```bash
kubectl apply -f k8s/phonebookapp.yaml
kubectl rollout status deployment/phonebookapp -n phonebook-app
```

### Deploy do Stack de Monitoramento

Instale Prometheus, Grafana e exporters de métricas:

```bash
# Prometheus
kubectl apply -f k8s/monitoring/prometheus.yaml

# Grafana com dashboards
kubectl apply -f k8s/monitoring/grafana.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml

# Exporters de métricas do Kubernetes
kubectl apply -f k8s/monitoring/kube-state-metrics.yaml
kubectl apply -f k8s/monitoring/node-exporter.yaml

# Aguarde todos os deployments
kubectl rollout status deployment/prometheus -n monitoring
kubectl rollout status deployment/grafana -n monitoring
kubectl rollout status deployment/kube-state-metrics -n monitoring
```

### Acessar os Serviços

Crie port-forwards para acessar localmente:

```bash
# Phonebook App
kubectl port-forward -n phonebook-app service/phonebookapp 3001:3000 &

# Prometheus
kubectl port-forward -n monitoring service/prometheus 9090:9090 &

# Grafana
kubectl port-forward -n monitoring service/grafana 3002:3000 &
```

Acesse:
- **Phonebook App**: [http://localhost:3001](http://localhost:3001)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3002](http://localhost:3002) (usuário: `admin`, senha: `admin`)

### Verificar Recursos

```bash
kubectl get all,pvc -n phonebook-app
kubectl get all,pvc -n monitoring
```

### Remover

```bash
kubectl delete -f k8s/phonebookapp.yaml
kubectl delete -f k8s/monitoring/
```

> O Deployment usa uma única réplica porque o SQLite armazena os dados em um
> único arquivo. Para escalar horizontalmente, substitua o SQLite por um banco
> como PostgreSQL.

## Observabilidade com Prometheus e Grafana

### Métricas Disponíveis

A aplicação expõe as seguintes métricas no endpoint `/metrics`:

| Métrica | Tipo | Descrição |
| --- | --- | --- |
| `phonebookapp_http_requests_total` | Counter | Total de requisições HTTP por método, endpoint e status |
| `phonebookapp_http_request_duration_seconds` | Histogram | Latência de requisições HTTP |
| `phonebookapp_http_requests_in_progress` | Gauge | Requisições HTTP em processamento |
| `phonebookapp_db_operations_total` | Counter | Total de operações no banco de dados |

### Dashboards do Grafana

Dois dashboards vêm pré-configurados:

#### 1. **Phonebook App Metrics**
- HTTP Request Rate (req/s)
- HTTP Request Duration (p95 e p50)
- HTTP Requests In Progress
- Database Operations Rate
- HTTP Status Codes
- Error Rate (4xx + 5xx)

#### 2. **Kubernetes Cluster Health**
- Cluster Overview (Total Nodes)
- Total Pods / Running Pods / Failed Pods
- CPU Usage by Node
- Memory Usage by Node
- Pods by Namespace
- Pod Restarts (Last 5m)
- Node Disk Usage
- Network I/O (RX/TX)
- Pod Status by Phase
- Deployments - Available vs Desired Replicas

### Consultar Métricas

**Via Prometheus**:
```bash
# Total de requisições
curl 'http://localhost:9090/api/v1/query?query=sum(phonebookapp_http_requests_total)'

# Taxa de requisições (últimos 5 minutos)
curl 'http://localhost:9090/api/v1/query?query=rate(phonebookapp_http_requests_total[5m])'
```

**Diretamente da aplicação**:
```bash
curl http://localhost:3001/metrics
```

### Configuração do Prometheus

O Prometheus está configurado para:
- **Scrape interval**: 15 segundos
- **Auto-discovery**: descobre automaticamente pods com a anotação `prometheus.io/scrape: "true"`
- **Retenção**: métricas são armazenadas em PVC de 10Gi

## Limitações e Considerações

### SQLite em Produção

- ⚠️ **Réplica única apenas**: o Deployment Kubernetes usa `replicas: 1` porque o SQLite armazena dados em um arquivo local que não pode ser compartilhado entre múltiplos pods
- ⚠️ **Strategy Recreate**: evita que múltiplas réplicas acessem o banco simultaneamente durante atualizações
- 💡 **Para escalar horizontalmente**: migre para PostgreSQL, MySQL ou outro SGBD que suporte múltiplos clientes concorrentes

### Feedback Storage

O endpoint `/api/feedback` apenas **armazena** o feedback no banco de dados. Não envia emails nem notificações. Para uso em produção:
- Integre com serviço de email (SendGrid, Mailgun, SES)
- Envie para sistema de tickets (Jira, Linear, GitHub Issues)
- Notifique via Slack/Discord webhooks

### Migrações de Schema

Não há framework de migrações implementado. Mudanças no schema do banco requerem:
- Execução manual de SQL ALTER TABLE
- Ou drop/recreate do volume (perde dados)

Para produção, considere usar **Alembic** ou **SQLAlchemy migrations**.

## Roadmap

Melhorias futuras planejadas:

- [ ] Suporte a PostgreSQL para escalabilidade horizontal
- [ ] Autenticação e multi-tenancy (usuários isolados)
- [ ] Importação/exportação de contatos (CSV, vCard)
- [ ] Favoritar contatos e categorias/tags
- [ ] Dark mode toggle
- [ ] PWA (Progressive Web App) com offline support
- [ ] Internacionalização (i18n) para múltiplos idiomas
- [ ] Notificações push para lembretes de aniversário
- [ ] Integração com serviços de notificação para feedback
- [ ] Alertas no Grafana para métricas críticas
- [ ] Distributed tracing com OpenTelemetry

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).

---

**Desenvolvido com ❤️ usando Python, Vanilla JS, Prometheus e Grafana**
