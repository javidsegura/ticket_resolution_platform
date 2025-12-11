## Create .env.dev file
In the same directory as this file, create a `.env.dev` file.
```bash
touch .env.dev
```

## Copy and paste this (substitute if needed)
```txt
# SET-UP
ENVIRONMENT="dev"


# REDIS
REDIS_URL="redis://redis:6379"


# DB
MYSQL_USER="root"
MYSQL_PASSWORD="rootpassword"
MYSQL_HOST="database"
MYSQL_PORT="3306"
MYSQL_DATABASE="ai_ticket_platform"
MYSQL_SYNC_DRIVER="mysql+pymysql"
MYSQL_ASYNC_DRIVER="mysql+aiomysql"

SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0... # zeffo-tickets channel @ CSAI teamazo
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL # For Grafana alerts to #telemetry

# LLM (Gemini)
GEMINI_API_KEY=""
GEMINI_MODEL="gemini-1.5-flash"

# AWS => not needed yet
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_MAIN_REGION=""
S3_MAIN_BUCKET_NAME=""
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/app/src/ai_ticket_platform/core/clients/secret.url-shortener-abadb-firebase-adminsdk-fbsvc-48d38c91f0.json.json
```

CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=company-docs
