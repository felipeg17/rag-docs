import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.dependencies import get_db_client
from main import app


class TestHealthRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_db_client = MagicMock()
        app.dependency_overrides[get_db_client] = lambda: self.mock_db_client

    def test_health_endpoint_returns_200(self):
        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_correct_message(self):
        # Arrange
        self.mock_db_client.heartbeat.return_value = True

        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.json(), {"status": "healthy", "database": "connected"})


if __name__ == "__main__":
    unittest.main()
