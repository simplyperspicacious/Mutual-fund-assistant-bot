import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Mocking RAG for API testing if needed, or using real one
from phase5_ui.api import app

client = TestClient(app)

class TestAPI(unittest.TestCase):
    def test_frontend_load(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mutual fund Assistant", response.text)

    def test_api_chat_valid(self):
        response = client.post("/api/chat", json={"query": "What is the exit load of Liquid Fund?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)

    def test_api_chat_empty(self):
        response = client.post("/api/chat", json={"query": ""})
        self.assertEqual(response.status_code, 400)

    def test_api_chat_guardrail(self):
        response = client.post("/api/chat", json={"query": "Should I invest?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("factual information", data["answer"])

if __name__ == "__main__":
    unittest.main()
