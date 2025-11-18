FROM  python:3.11-slim


RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

ENV APP_PATH="src.ai_ticket_platform.main:app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./src ./src
RUN pip3 install --no-cache-dir .


COPY ./alembic.ini ./
COPY ./scripts ./scripts

EXPOSE 8000

CMD ["sh", "-c", "gunicorn $APP_PATH --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --log-level debug --access-logfile - --error-logfile - --preload --enable-stdio-inheritance"]
