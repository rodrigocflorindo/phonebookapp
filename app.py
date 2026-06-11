import json
import os
import re
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "contacts.db"))
PHONE_PATTERN = re.compile(r"^[0-9()+\-\s]{8,20}$")


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


class ContactHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

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

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"status": "ok"})
            return

        if path == "/api/contacts":
            with get_connection() as connection:
                contacts = connection.execute(
                    "SELECT id, name, phone, created_at FROM contacts ORDER BY name COLLATE NOCASE"
                ).fetchall()
            self.send_json([dict(contact) for contact in contacts])
            return

        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/contacts":
            self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)
            return

        contact, error = self.validate_contact(self.read_json())
        if error:
            self.send_json({"error": error}, HTTPStatus.BAD_REQUEST)
            return

        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO contacts (name, phone) VALUES (?, ?)",
                (contact["name"], contact["phone"]),
            )
            created = connection.execute(
                "SELECT id, name, phone, created_at FROM contacts WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        self.send_json(dict(created), HTTPStatus.CREATED)

    def do_PUT(self):
        contact_id = self.contact_id()
        if contact_id is None:
            self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)
            return

        contact, error = self.validate_contact(self.read_json())
        if error:
            self.send_json({"error": error}, HTTPStatus.BAD_REQUEST)
            return

        with get_connection() as connection:
            cursor = connection.execute(
                "UPDATE contacts SET name = ?, phone = ? WHERE id = ?",
                (contact["name"], contact["phone"], contact_id),
            )
            if cursor.rowcount == 0:
                self.send_json({"error": "Contato não encontrado."}, HTTPStatus.NOT_FOUND)
                return
            updated = connection.execute(
                "SELECT id, name, phone, created_at FROM contacts WHERE id = ?",
                (contact_id,),
            ).fetchone()
        self.send_json(dict(updated))

    def do_DELETE(self):
        contact_id = self.contact_id()
        if contact_id is None:
            self.send_json({"error": "Rota não encontrada."}, HTTPStatus.NOT_FOUND)
            return

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
