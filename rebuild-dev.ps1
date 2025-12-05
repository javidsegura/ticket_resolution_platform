# Rebuild and start development environment
$env:ENVIRONMENT = "dev"
$env:BACKEND_ENV_FILE = "../backend/.env"

Set-Location -Path "deployment"
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
Set-Location -Path ".."
