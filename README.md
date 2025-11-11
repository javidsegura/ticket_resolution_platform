# ticket_resolution_platform
AI-Powered Ticket Resolution Platform

## Set-up
### Dependencies 
1. Every time you run make targets you need to set up the environment you are working at:
`export ENVIRONMENT=""` value can be between ["test", "dev", "staging", "prod"]
2. Install packages dependencies: 
   - Project-wide dependencies:  make install at the root level
   - Frontend dependencies:  make install after cd frontend/
   - Backend dependencies:  make install  after cd backend/
   - Infra dependencies:  make install  after cd infra/
      - Note: you will need to set-up: `export CLOUD_PROVIDER=""` value can be between ["aws", "azure"]
3. Install docker dependices:
   - You may need to install multi-platform iamge from Docker if you face issues with images from docker being installed for a different
     architecture. In order to do that you just need to do the following:
    `docker buildx build --platform linux/amd64,linux/arm64 -t javidsegura/url_shortener_backend --push ./backend` 
### Secrets 
- Backend: 
  - Write in "backend/src/ai_ticket_platform/core/clients/secret.ai_ticket_platform-abadb-firebase-adminsdk-fbsvc-48d38c91f0.json" the corresponding firebase key
- 

### Environmental variables 

- Each environment has their own needs for environmental variables, chekc them in src/settings/environment
- OPEN_ROUTER_API_KEY => you will probably need this key. Register [here](https://openrouter.ai/) to get one.

### Makefiles
- Most of the names of the Makefile targets are self-descriptive. 
- For now on, you will most likely just use `make dev-start` 

## References
Business, MVP, Sprints: [link](https://docs.google.com/document/d/1GDx8ERpdd2Bapt1hQfTBkYGhXiyvSLgq6holw6LnoTM/edit?usp=sharing)
See docs folder to access more docs: [docs](docs/)