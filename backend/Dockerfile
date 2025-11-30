FROM python:3.11-slim

# 1. Install curl (for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 2. Install uv using pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Configure Environment
ENV  APP_PATH="src.ai_ticket_platform.main:app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# 4. Install Dependencies (The "Cached" Layer)
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r pyproject.toml

# 5. Install Application (The "Editable" Layer)
COPY ./src ./src
RUN uv pip install -e .

# 6. Finalize
COPY ./alembic.ini ./
COPY ./scripts ./scripts

EXPOSE 8000

CMD ["sh", "-c", "gunicorn $APP_PATH --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --log-level debug --access-logfile - --error-logfile - --preload --enable-stdio-inheritance"]
