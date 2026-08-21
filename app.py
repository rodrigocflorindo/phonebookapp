import json
import os
import re
import sqlite3
from functools import wraps
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus metrics
http_requests_total = Counter(
    'phonebookapp_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'phonebookapp_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'phonebookapp_http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

db_operations_total = Counter(
    'phonebookapp_db_operations_total',
    'Total database operations',
    ['operation', 'table']
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "contacts.db"))
PHONE_PATTERN = re.compile(r"^[0-9()+\-\s]{8,20}$")


def request_resource(method, path):
    if path == "/api/contacts":
        return f"{method} /api/contacts"
    if re.fullmatch(r"/api/contacts/\d+", path):
        return f"{method} /api/contacts/{'{id}'}"
    if path == "/api/health":
        return f"{method} /api/health"
    if path == "/api/feedback":
        return f"{method} /api/feedback"
    return f"{method} static"


def traced_request(handler):
    @wraps(handler)
    def wrapper(self, *args, **kwargs):
        path = urlparse(self.path).path
        method = self.command
        endpoint = request_resource(method, path)

        # Skip tracing and detailed metrics for health checks and metrics endpoint
        if path in ["/api/health", "/metrics"]:
            return handler(self, *args, **kwargs)

        # Prometheus: track requests in progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        try:
            # Prometheus: measure request duration
            with http_request_duration_seconds.labels(method=method, endpoint=endpoint).time():
                return handler(self, *args, **kwargs)
        finally:
            # Prometheus: decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    return wrapper


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


class ContactHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def send_response(self, code, message=None):
        # Prometheus: count HTTP requests by status
        path = urlparse(self.path).path
        if path != "/api/health" and path != "/metrics":
            method = self.command
            endpoint = request_resource(method, path)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=code
            ).inc()

        super().send_response(code, message)

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(content_length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def contact_id(self):
        match = re.fullmatch(r"/api/contacts/(\d+)", urlparse(self.path).path)
        return int(match.group(1)) if match else None

    def validate_contact(self, payload):
        if not isinstance(payload, dict):
            return None, "Envie um JSON válido."

        name = str(payload.get("name", "")).strip()
        phone = str(payload.get("phone", "")).strip()

        if len(name) < 2 or len(name) > 80:
            return None, "O nome deve ter entre 2 e 80 caracteres."
        if not PHONE_PATTERN.fullmatch(phone):
            return None, "Informe um telefone válido com 8 a 20 caracteres."

        return {"name": name, "phone": phone}, None

    def validate_feedback(self, payload):
        if not isinstance(payload, dict):
            return None, "Envie um JSON válido."

        email = payload.get("email")
        message = str(payload.get("message", "")).strip()

        if email is not None:
            email = str(email).strip()
            if email and (len(email) > 100 or "@" not in email):
                return None, "Informe um e-mail válido com até 100 caracteres."
            email = email if email else None

        if len(message) < 10 or len(message) > 500:
            return None, "A mensagem deve ter entre 10 e 500 caracteres."

        return {"email": email, "message": message}, None

    @traced_request
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"status": "ok"})
            return

        if path == "/metrics":
            # Prometheus metrics endpoint
            metrics = generate_latest()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(metrics)))
            self.end_headers()
            self.wfile.write(metrics)
            return

        if path == "/api/contacts":
            db_operations_total.labels(operation='SELECT', table='contacts').inc()
            with get_connection() as connection:
                contacts = connection.execute(
                    "SELECT id, name, phone, created_at FROM contacts ORDER BY name COLLATE NOCASE"
                ).fetchall()
            self.send_json([dict(contact) for contact in contacts])
            return

        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    @traced_request
    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/contacts":
            contact, error = self.validate_contact(self.read_json())
            if error:
                self.send_json({"error": error}, HTTPStatus.BAD_REQUEST)
                return

            db_operations_total.labels(operation='INSERT', table='contacts').inc()
            with get_connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO contacts (name, phone) VALUES (?, ?)",
                    (contact["name"], contact["phone"]),
                )
                db_operations_total.labels(operation='SELECT', table='contacts').inc()
                created = connection.execute(
                    "SELECT id, name, phone, created_at FROM contacts WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
            self.send_json(dict(created), HTTPStatus.CREATED)
            return

        if path == "/api/feedback":
            feedback, error = self.validate_feedback(self.read_json())
            if error:
                self.send_json({"error": error}, HTTPStatus.BAD_REQUEST)
                return

            db_operations_total.labels(operation='INSERT', table='feedback').inc()
            with get_connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO feedback (email, message) VALUES (?, ?)",
                    (feedback["email"], feedback["message"]),
                )
                db_operations_total.labels(operation='SELECT', table='feedback').inc()
                created = connection.execute(
                    "SELECT id, email, message, created_at FROM feedback WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
            self.send_json(dict(created), HTTPStatus.CREATED)
            return

        self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)

    @traced_request
    def do_PUT(self):
        contact_id = self.contact_id()
        if contact_id is None:
            self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)
            return

        contact, error = self.validate_contact(self.read_json())
        if error:
            self.send_json({"error": error}, HTTPStatus.BAD_REQUEST)
            return

        db_operations_total.labels(operation='UPDATE', table='contacts').inc()
        with get_connection() as connection:
            cursor = connection.execute(
                "UPDATE contacts SET name = ?, phone = ? WHERE id = ?",
                (contact["name"], contact["phone"], contact_id),
            )
            if cursor.rowcount == 0:
                self.send_json({"error": "Contato não encontrado."}, HTTPStatus.NOT_FOUND)
                return
            db_operations_total.labels(operation='SELECT', table='contacts').inc()
            updated = connection.execute(
                "SELECT id, name, phone, created_at FROM contacts WHERE id = ?",
                (contact_id,),
            ).fetchone()
        self.send_json(dict(updated))

    @traced_request
    def do_DELETE(self):
        contact_id = self.contact_id()
        if contact_id is None:
            self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)
            return

        db_operations_total.labels(operation='DELETE', table='contacts').inc()
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            if cursor.rowcount == 0:
                self.send_json({"error": "Contato não encontrado."}, HTTPStatus.NOT_FOUND)
                return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()


if __name__ == "__main__":
    initialize_database()
    port = int(os.getenv("PORT", "3000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ContactHandler)
    print(f"Agenda disponível em http://localhost:{port}", flush=True)
    server.serve_forever()
