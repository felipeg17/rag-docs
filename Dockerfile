FROM python:3.10-slim

USER root

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

WORKDIR /ms
COPY app /ms/app
COPY main.py /ms/

EXPOSE 8106

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8106"]