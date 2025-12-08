import unittest

from fastapi.testclient import TestClient

from main import app


class TestHealthRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint_returns_200(self):
        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_correct_message(self):
        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.json(), {"status": "healthy"})


if __name__ == "__main__":
    unittest.main()
