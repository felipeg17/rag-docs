import os


def load_backend_config() -> str:
    backend_host = os.getenv("API_HOST")
    backend_port = os.getenv("API_PORT")
    if not backend_host or not backend_port:
        raise ValueError("API_HOST and API_PORT environment variables must be set.")
    return f"http://{backend_host}:{backend_port}/"
