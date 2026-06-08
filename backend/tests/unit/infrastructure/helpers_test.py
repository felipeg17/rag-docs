import os
import unittest
from unittest.mock import MagicMock, patch

import requests
from google.api_core.exceptions import GoogleAPIError

from app.core.helpers import _get_gcp_project_id, get_secret


class TestGetGcpProjectId(unittest.TestCase):
    def setUp(self):
        _get_gcp_project_id.cache_clear()

    def tearDown(self):
        _get_gcp_project_id.cache_clear()

    @patch("app.core.helpers.requests.get")
    def test_returns_project_id_from_metadata_server(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "my-gcp-project"
        mock_get.return_value = mock_response

        result = _get_gcp_project_id()

        self.assertEqual(result, "my-gcp-project")

    @patch.dict(os.environ, {"PROJECT_ID": "local-project"})
    @patch("app.core.helpers.requests.get", side_effect=requests.RequestException("timeout"))
    def test_falls_back_to_env_var_when_metadata_server_unreachable(self, _):
        result = _get_gcp_project_id()

        self.assertEqual(result, "local-project")

    @patch("app.core.helpers.requests.get", side_effect=requests.RequestException("timeout"))
    def test_returns_empty_string_when_metadata_unreachable_and_env_var_absent(self, _):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PROJECT_ID", None)
            result = _get_gcp_project_id()

        self.assertEqual(result, "")


class TestGetSecret(unittest.TestCase):
    def setUp(self):
        get_secret.cache_clear()

    def tearDown(self):
        get_secret.cache_clear()

    @patch.dict(os.environ, {"USE_SECRETS": "false", "OPENAI_API_KEY": "sk-test-key"})
    def test_returns_env_var_when_use_secrets_false(self):
        result = get_secret("openai-api-key")

        self.assertEqual(result, "sk-test-key")

    @patch.dict(os.environ, {"USE_SECRETS": "false"})
    def test_returns_empty_string_when_env_var_missing(self):
        os.environ.pop("OPENAI_API_KEY", None)

        result = get_secret("openai-api-key")

        self.assertEqual(result, "")

    @patch("app.core.helpers._get_gcp_project_id", return_value="test-project")
    @patch("app.core.helpers.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"USE_SECRETS": "true"})
    def test_returns_secret_from_secret_manager(self, mock_client_class, _):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.payload.data = b"super-secret-value"
        mock_client.access_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = get_secret("openai-api-key")

        self.assertEqual(result, "super-secret-value")
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/test-project/secrets/openai-api-key/versions/latest"}
        )

    @patch("app.core.helpers._get_gcp_project_id", return_value="test-project")
    @patch("app.core.helpers.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"USE_SECRETS": "true"})
    def test_raises_on_google_api_error(self, mock_client_class, _):
        mock_client = MagicMock()
        mock_client.access_secret_version.side_effect = GoogleAPIError("Permission denied")
        mock_client_class.return_value = mock_client

        with self.assertRaises(GoogleAPIError):
            get_secret("openai-api-key")

    @patch("app.core.helpers._get_gcp_project_id", return_value="test-project")
    @patch("app.core.helpers.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"USE_SECRETS": "true", "OPENAI_API_KEY": "fallback-key"})
    def test_falls_back_to_env_var_on_unexpected_exception(self, mock_client_class, _):
        mock_client = MagicMock()
        mock_client.access_secret_version.side_effect = RuntimeError("Unexpected")
        mock_client_class.return_value = mock_client

        result = get_secret("openai-api-key")

        self.assertEqual(result, "fallback-key")

    @patch("app.core.helpers._get_gcp_project_id", return_value="test-project")
    @patch("app.core.helpers.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"USE_SECRETS": "true"})
    def test_raises_when_exception_and_env_var_also_missing(self, mock_client_class, _):
        mock_client = MagicMock()
        mock_client.access_secret_version.side_effect = RuntimeError("Unexpected")
        mock_client_class.return_value = mock_client
        os.environ.pop("OPENAI_API_KEY", None)

        with self.assertRaises(RuntimeError):
            get_secret("openai-api-key")


if __name__ == "__main__":
    unittest.main()
