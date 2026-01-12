import os

from behave.runner import Context  # type: ignore


def before_all(context: Context) -> None:
    """Setup test environment before all scenarios."""
    context.vectordb_url = os.getenv("CHROMADB_URL", "http://localhost:9001")
    context.backend_url = os.getenv("BACKEND_URL", "http://localhost:8106")


def after_scenario(context: Context, scenario) -> None:
    """Cleanup after each scenario."""
    pass
