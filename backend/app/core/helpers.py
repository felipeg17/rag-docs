import os
from enum import Enum
from functools import lru_cache

import requests
from google.api_core.exceptions import GoogleAPIError
from google.cloud import secretmanager

from app.utils.logger import logger


class VectorDBType(str, Enum):
    CHROMA = "chroma"
    PGVECTOR = "pgvector"


@lru_cache(maxsize=10)
def _get_gcp_project_id() -> str:
    """Get GCP project ID from metadata server (works in Cloud Run) or env var."""
    try:
        # (Cloud Run, Compute Engine)
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
            timeout=1,
        )
        response.raise_for_status()
        return response.text

    except requests.RequestException:
        logger.info("Not running in GCP environment, retrieving project_id from local environment.")
        return os.getenv("PROJECT_ID", "")

    except Exception as e:
        logger.info(f"Exception: {e}")
        logger.info("Running locally, retrieving project_id using local environment.")
        return os.getenv("PROJECT_ID", "")


@lru_cache(maxsize=10)
def get_secret(secret_id: str) -> str:
    """Fetch secret from GCP Secret Manager. Cached."""
    # Check if running locally first (fast path)
    use_gcp_secrets = os.getenv("USE_SECRETS", "false").lower() == "true"

    if not use_gcp_secrets:
        logger.info(f"Using local environment variable for secret: {secret_id}")
        env_var = os.getenv(secret_id.upper().replace("-", "_"))
        if env_var:
            return env_var
        else:
            logger.warning(f"Secret {secret_id} not found in local environment.")

    try:
        project_id = _get_gcp_project_id()
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    except GoogleAPIError:
        logger.error(f"Secret {secret_id} not found in GCP Secret Manager.")
        raise

    except Exception as e:
        logger.info(f"Exception: {e}")
        logger.info("Trying to retrieve as an env variable as a fallback")
        env_var = os.getenv(secret_id.upper().replace("-", "_"))
        if env_var:
            return env_var
        else:
            logger.error("Secret {secret_id} not found in local environment.")
            raise
