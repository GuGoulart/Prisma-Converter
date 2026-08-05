import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

class TestAPI(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data.get("status"), "ok")

    def test_security_headers(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        headers = res.headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_paginas_principais(self):
        for path in ["/", "/conversor", "/ferramentas-avancadas", "/modificar-arquivos", "/historico"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Rota {path} falhou com código {res.status_code}")

if __name__ == "__main__":
    unittest.main()
