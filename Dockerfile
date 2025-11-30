# Builder - Install dependencies
FROM python:3.10-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /ms

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# Runtime
FROM python:3.10-slim

WORKDIR /ms

COPY --from=builder /ms/.venv /ms/.venv

COPY app /ms/app
COPY main.py /ms/
COPY .env.backend /ms/.env

# PYTHON PATH
ENV PATH="/ms/.venv/bin:$PATH"

EXPOSE 8106

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8106"]