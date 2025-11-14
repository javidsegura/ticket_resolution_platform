# ticket_resolution_platform
AI-Powered Ticket Resolution Platform

## Set-up
### Dependencies 
1. Every time you run make targets you need to set up the environment you are working at:
`export ENVIRONMENT=""` value can be between ["test", "dev", "staging", "prod"]
2. Install packages dependencies: 
   - Project-wide dependencies:  make install at the root level
   - Frontend dependencies:  make -C frontend install
   - Backend dependencies:  make -C backend install   
   - Infra dependencies (**only if working in infra**):  make install  after cd infra/
      - Notes: 
        - You will need to set-up: `export CLOUD_PROVIDER=""` value can be between ["aws", "azure"]
3. Install docker dependices:
   - You may need to install multi-platform iamge from Docker if you face issues with images from docker being installed for a different
     architecture. In order to do that you just need to do the following:
    `docker buildx build --platform linux/amd64,linux/arm64 -t javidsegura/url_shortener_backend --push ./backend` 
### Secrets 
- Backend: 
  - Copy to backend/env_config/synced/.env.dev:
```bash
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


# AWS => not needed yet
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY="" 
AWS_MAIN_REGION=""
S3_MAIN_BUCKET_NAME=""
```

- Frontend:
```bash
apiKey="",
authDomain="",
projectId="",
storageBucket="",
messagingSenderId="",
appId="",
measurementId=""
VITE_BASE_URL=http://localhost/api/
```
### Environmental variables 

- Each environment has their own needs for environmental variables, chekc them in src/settings/environment
- OPEN_ROUTER_API_KEY => you will probably need this key. Register [here](https://openrouter.ai/) to get one.

### Makefiles
- Most of the names of the Makefile targets are self-descriptive. 
- For now on, you will most likely just use `make dev-start` 

## References
Business, MVP, Sprints: [link](https://docs.google.com/document/d/1GDx8ERpdd2Bapt1hQfTBkYGhXiyvSLgq6holw6LnoTM/edit?usp=sharing)
See docs folder to access more docs: [docs](docs/)
