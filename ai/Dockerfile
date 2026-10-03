FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    STORAGE_ROOT=/app/runtime-data

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-backend.txt requirements-ai.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt \
    && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-ai.txt

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./.env.example ./
COPY configs ./configs
COPY outputs ./outputs

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/runtime-data \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "herstyle_ai.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
