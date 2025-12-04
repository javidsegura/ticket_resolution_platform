export ENVIRONMENT="dev"
export BACKEND_ENV_FILE="../backend/.env"

cd deployment
# Source the variables so docker compose can see them (excluding comments and empty lines)
export $(grep -v '^#' ../backend/.env | grep -v '^$' | xargs)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
cd ..
