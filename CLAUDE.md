# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Phonebook App is a simple web-based contact management application that allows users to create, search, edit, and delete contacts. The application consists of:

- **Backend**: Python 3.12 HTTP server (`app.py`) serving static files and a REST API
- **Frontend**: Vanilla HTML, CSS, JavaScript in `static/` directory
- **Database**: SQLite database (`contacts.db`) with a single `contacts` table
- **Monitoring**: Datadog APM integration via `ddtrace` for distributed tracing

## Architecture

The application uses Python's `SimpleHTTPRequestHandler` to serve both static files and handle API requests. All API routes are prefixed with `/api/`. The backend uses a custom `traced_request` decorator to instrument HTTP requests with Datadog APM spans, excluding `/api/health` from tracing to avoid noise from probes.

**Database schema**:
```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Key architectural decisions**:
- Single-file Python application using standard library HTTP server with threading support
- SQLite with `row_factory = sqlite3.Row` to return dictionary-like rows
- Validation happens both client-side (JavaScript) and server-side (Python)
- Datadog tracing is patched at module level with `patch(sqlite3=True)`

## Development Commands

### Local development with Docker Compose

Start the application:
```bash
docker compose up -d --build
```

Access at http://localhost:3001

Stop the application:
```bash
docker compose down
```

Remove application and database:
```bash
docker compose down -v
```

### Kubernetes deployment (GIRUS cluster)

Set context to GIRUS cluster:
```bash
kubectl config use-context kind-girus
```

Build and load image:
```bash
docker build -t phonebookapp:1.0.0 .
kind load docker-image phonebookapp:1.0.0 --name girus
```

Deploy to cluster:
```bash
kubectl apply -f k8s/phonebookapp.yaml
kubectl rollout status deployment/phonebookapp -n phonebook-app
```

Port forward to access locally:
```bash
kubectl port-forward -n phonebook-app service/phonebookapp 3001:3000
```

Check resources:
```bash
kubectl get all,pvc -n phonebook-app
```

Remove deployment:
```bash
kubectl delete -f k8s/phonebookapp.yaml
```

### Testing the API

Health check:
```bash
curl http://localhost:3001/api/health
```

List contacts:
```bash
curl http://localhost:3001/api/contacts
```

Create contact:
```bash
curl -X POST http://localhost:3001/api/contacts \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria Silva","phone":"(11) 99999-9999"}'
```

Update contact:
```bash
curl -X PUT http://localhost:3001/api/contacts/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria Souza","phone":"(11) 98888-8888"}'
```

Delete contact:
```bash
curl -X DELETE http://localhost:3001/api/contacts/1
```

Submit feedback:
```bash
curl -X POST http://localhost:3001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","message":"Great app, very useful!"}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (not traced) |
| `GET` | `/api/contacts` | List all contacts ordered by name |
| `POST` | `/api/contacts` | Create a new contact |
| `PUT` | `/api/contacts/{id}` | Update an existing contact |
| `DELETE` | `/api/contacts/{id}` | Delete a contact |
| `POST` | `/api/feedback` | Submit user feedback |

## Validation Rules

**Name validation**:
- Must be between 2 and 80 characters
- Whitespace is trimmed

**Phone validation**:
- Must be between 8 and 20 characters
- Accepts: digits, spaces, `+`, `(`, `)`, `-`
- Regex pattern: `^[0-9()+\-\s]{8,20}$`

**Feedback validation**:
- Email: optional, up to 100 characters, must contain `@` if provided
- Message: required, between 10 and 500 characters
- Empty email strings are converted to `NULL` in the database

Validation errors return HTTP 400 with JSON error messages.

## Environment Variables

- `DATABASE_PATH`: Path to SQLite database file (default: `data/contacts.db`)
- `PORT`: HTTP server port (default: `3000`)
- `DD_AGENT_HOST`: Datadog Agent hostname (set to `host.docker.internal` in Docker Compose)
- `DD_ENV`: Environment tag for Datadog (e.g., `local`)
- `DD_SERVICE`: Service name for Datadog APM (`phonebookapp`)
- `DD_VERSION`: Version tag for Datadog (e.g., `1.1.1`)
- `DD_LOGS_INJECTION`: Enable log correlation (`true`)
- `DD_TRACE_SAMPLE_RATE`: Trace sampling rate (`1.0` for 100%)

## Datadog APM

The application sends traces to Datadog APM. After generating traffic, filter traces in Datadog:
```
service:phonebookapp env:local
```

To verify trace reception in the Kubernetes cluster:
```bash
kubectl exec -n default daemonset/datadog-agent -c agent -- agent status
```

Check the `APM Agent` section for non-zero `Traces` counter.

**Trace resource naming**:
- `GET /api/contacts` → resource: `GET /api/contacts`
- `PUT /api/contacts/123` → resource: `PUT /api/contacts/{id}`
- `POST /api/feedback` → resource: `POST /api/feedback`
- `GET /api/health` → not traced (excluded from instrumentation)

## Testing

Run the automated test suite:
```bash
python3 -m unittest test_app.py -v
```

The test suite includes:
- Contact CRUD operations
- Input validation for contacts
- Feedback submission with and without email
- Feedback validation (message length, email format)
- Database persistence verification

## Constraints and Limitations

- **Single replica only**: The Kubernetes deployment uses `replicas: 1` because SQLite stores data in a single file that cannot be shared across multiple pods. To scale horizontally, migrate to PostgreSQL or another multi-client database.
- **No migrations framework**: Database schema changes require manual SQL execution or dropping and recreating the database.
- **Recreate deployment strategy**: The Kubernetes deployment uses `type: Recreate` to avoid multiple replicas accessing the SQLite file simultaneously.
- **Feedback storage only**: The feedback endpoint stores data but does not send notifications or emails. For production use, integrate with a notification system.

## File Structure

```
phonebookapp/
├── app.py              # Python HTTP server and API logic
├── static/
│   ├── index.html      # Main HTML interface
│   ├── app.js          # Frontend JavaScript logic
│   └── styles.css      # Responsive CSS styles
├── docs/
│   ├── API.md          # API usage examples
│   └── phonebook-app.png
├── k8s/
│   └── phonebookapp.yaml  # Kubernetes manifests (Namespace, PVC, Deployment, Service)
├── Dockerfile          # Multi-stage Docker build
├── compose.yaml        # Docker Compose configuration
├── requirements.txt    # Python dependencies (ddtrace only)
└── README.md           # Project documentation
```

## License

Distributed under the MIT License. See [LICENSE](LICENSE) file for details.
