"""Export the FastAPI OpenAPI schema offline to ``openapi.json`` (frontend type source)."""

import json
from pathlib import Path

from main import app


SNAPSHOT = Path(__file__).with_name("openapi.json")


def render() -> str:
    """Return the app's OpenAPI schema as deterministic JSON text."""
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    SNAPSHOT.write_text(render(), encoding="utf-8")
