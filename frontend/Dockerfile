# Builder - Install dependencies
FROM python:3.10-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev


# Runtime
FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Necessary folders
COPY front.py /app/
COPY components /app/components
COPY pages /app/pages
COPY utils /app/utils
COPY src /app/src
COPY data /app/data
COPY frontend.env /app/.env

ENV PATH="/app/.venv/bin:$PATH"

# Configure Streamlit
RUN mkdir -p /root/.streamlit && \
    echo '[server]\n\
    port = 8502\n\
    address = "0.0.0.0"\n\
    headless = true\n\
    enableCORS = false\n\
    enableXsrfProtection = false\n' > /root/.streamlit/config.toml

EXPOSE 8502


CMD ["streamlit", "run", "front.py", "--server.port=8502", "--server.address=0.0.0.0"]