import json
import os
import sqlite3
import tempfile
import unittest
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from time import sleep

import app


class PhonebookAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = Path(cls.temp_dir) / "test_contacts.db"
        os.environ["DATABASE_PATH"] = str(cls.db_path)
        os.environ["PORT"] = "3333"

        app.DATABASE_PATH = cls.db_path
        app.initialize_database()

        cls.server_thread = Thread(
            target=lambda: app.ThreadingHTTPServer(("127.0.0.1", 3333), app.ContactHandler).serve_forever(),
            daemon=True
        )
        cls.server_thread.start()
        sleep(0.5)

        cls.conn = HTTPConnection("127.0.0.1", 3333, timeout=5)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def setUp(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("DELETE FROM contacts")
            connection.execute("DELETE FROM feedback")

    def request(self, method, path, body=None):
        headers = {"Content-Type": "application/json"} if body else {}
        self.conn.request(method, path, body=json.dumps(body) if body else None, headers=headers)
        response = self.conn.getresponse()
        data = response.read()
        return response.status, json.loads(data) if data else None

    def test_health_endpoint(self):
        status, data = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"status": "ok"})

    def test_create_contact_success(self):
        status, data = self.request("POST", "/api/contacts", {"name": "João Silva", "phone": "(11) 98765-4321"})
        self.assertEqual(status, 201)
        self.assertIn("id", data)
        self.assertEqual(data["name"], "João Silva")
        self.assertEqual(data["phone"], "(11) 98765-4321")

    def test_create_contact_validation_name_too_short(self):
        status, data = self.request("POST", "/api/contacts", {"name": "A", "phone": "(11) 98765-4321"})
        self.assertEqual(status, 400)
        self.assertIn("nome", data["error"].lower())

    def test_create_contact_validation_phone_invalid(self):
        status, data = self.request("POST", "/api/contacts", {"name": "João Silva", "phone": "123"})
        self.assertEqual(status, 400)
        self.assertIn("telefone", data["error"].lower())

    def test_list_contacts(self):
        self.request("POST", "/api/contacts", {"name": "Maria Santos", "phone": "(21) 99999-8888"})
        self.request("POST", "/api/contacts", {"name": "Pedro Costa", "phone": "(31) 97777-6666"})

        status, data = self.request("GET", "/api/contacts")
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Maria Santos")
        self.assertEqual(data[1]["name"], "Pedro Costa")

    def test_update_contact_success(self):
        _, created = self.request("POST", "/api/contacts", {"name": "Ana Lima", "phone": "(41) 96666-5555"})
        contact_id = created["id"]

        status, data = self.request("PUT", f"/api/contacts/{contact_id}", {"name": "Ana Souza", "phone": "(41) 95555-4444"})
        self.assertEqual(status, 200)
        self.assertEqual(data["name"], "Ana Souza")
        self.assertEqual(data["phone"], "(41) 95555-4444")

    def test_update_contact_not_found(self):
        status, data = self.request("PUT", "/api/contacts/9999", {"name": "Teste", "phone": "(11) 99999-9999"})
        self.assertEqual(status, 404)
        self.assertIn("não encontrado", data["error"].lower())

    def test_delete_contact_success(self):
        _, created = self.request("POST", "/api/contacts", {"name": "Carlos Alberto", "phone": "(51) 94444-3333"})
        contact_id = created["id"]

        status, data = self.request("DELETE", f"/api/contacts/{contact_id}")
        self.assertEqual(status, 204)
        self.assertIsNone(data)

        status, contacts = self.request("GET", "/api/contacts")
        self.assertEqual(len(contacts), 0)

    def test_delete_contact_not_found(self):
        status, data = self.request("DELETE", "/api/contacts/9999")
        self.assertEqual(status, 404)
        self.assertIn("não encontrado", data["error"].lower())

    def test_create_feedback_success_with_email(self):
        status, data = self.request("POST", "/api/feedback", {
            "email": "usuario@example.com",
            "message": "Aplicativo muito útil, parabéns!"
        })
        self.assertEqual(status, 201)
        self.assertIn("id", data)
        self.assertEqual(data["email"], "usuario@example.com")
        self.assertEqual(data["message"], "Aplicativo muito útil, parabéns!")
        self.assertIn("created_at", data)

    def test_create_feedback_success_without_email(self):
        status, data = self.request("POST", "/api/feedback", {
            "email": None,
            "message": "Sugestão: adicionar filtro por data de criação."
        })
        self.assertEqual(status, 201)
        self.assertIn("id", data)
        self.assertIsNone(data["email"])
        self.assertEqual(data["message"], "Sugestão: adicionar filtro por data de criação.")

    def test_create_feedback_success_with_empty_email(self):
        status, data = self.request("POST", "/api/feedback", {
            "email": "",
            "message": "Feedback anônimo funciona perfeitamente!"
        })
        self.assertEqual(status, 201)
        self.assertIsNone(data["email"])

    def test_create_feedback_validation_message_too_short(self):
        status, data = self.request("POST", "/api/feedback", {
            "email": "test@test.com",
            "message": "Curto"
        })
        self.assertEqual(status, 400)
        self.assertIn("mensagem", data["error"].lower())
        self.assertIn("10", data["error"])

    def test_create_feedback_validation_message_too_long(self):
        long_message = "A" * 501
        status, data = self.request("POST", "/api/feedback", {
            "email": None,
            "message": long_message
        })
        self.assertEqual(status, 400)
        self.assertIn("mensagem", data["error"].lower())
        self.assertIn("500", data["error"])

    def test_create_feedback_validation_invalid_email(self):
        status, data = self.request("POST", "/api/feedback", {
            "email": "invalid-email",
            "message": "Esta mensagem tem mais de 10 caracteres."
        })
        self.assertEqual(status, 400)
        self.assertIn("e-mail", data["error"].lower())

    def test_create_feedback_validation_email_too_long(self):
        long_email = "a" * 95 + "@b.com"
        status, data = self.request("POST", "/api/feedback", {
            "email": long_email,
            "message": "Mensagem de teste com mais de 10 caracteres."
        })
        self.assertEqual(status, 400)
        self.assertIn("e-mail", data["error"].lower())

    def test_create_feedback_validation_invalid_json(self):
        headers = {"Content-Type": "application/json"}
        self.conn.request("POST", "/api/feedback", body="não é json", headers=headers)
        response = self.conn.getresponse()
        data = json.loads(response.read())
        self.assertEqual(response.status, 400)
        self.assertIn("json", data["error"].lower())

    def test_feedback_stored_in_database(self):
        self.request("POST", "/api/feedback", {
            "email": "user1@test.com",
            "message": "Primeiro feedback de teste."
        })
        self.request("POST", "/api/feedback", {
            "email": None,
            "message": "Segundo feedback anônimo."
        })

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            feedbacks = connection.execute("SELECT * FROM feedback ORDER BY id").fetchall()

        self.assertEqual(len(feedbacks), 2)
        self.assertEqual(feedbacks[0]["email"], "user1@test.com")
        self.assertEqual(feedbacks[0]["message"], "Primeiro feedback de teste.")
        self.assertIsNone(feedbacks[1]["email"])
        self.assertEqual(feedbacks[1]["message"], "Segundo feedback anônimo.")


if __name__ == "__main__":
    unittest.main()
