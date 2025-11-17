# CLAUDE.md - Project Coding Standards & Conventions

This document defines the coding standards, architectural patterns, and conventions used in the AI Ticket Resolution Platform. **Follow these patterns strictly** to ensure consistency across the codebase.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Backend Patterns (FastAPI)](#backend-patterns-fastapi)
5. [Frontend Patterns (React/TypeScript)](#frontend-patterns-reacttypescript)
6. [Configuration Management](#configuration-management)
7. [Database Patterns](#database-patterns)
8. [Client Initialization Patterns](#client-initialization-patterns)
9. [Dependency Injection Patterns](#dependency-injection-patterns)
10. [Infrastructure Patterns](#infrastructure-patterns)
11. [Code Quality & Standards](#code-quality--standards)
12. [Git & PR Conventions](#git--pr-conventions)
13. [Development Workflow](#development-workflow)
14. [Testing Standards](#testing-standards)

---

## Project Overview

This is an AI-Powered Ticket Resolution Platform with:
- **Backend**: FastAPI (Python) with async/await patterns
- **Frontend**: React 19 with TypeScript
- **Database**: MySQL (async via aiomysql)
- **Cache**: Redis
- **Infrastructure**: Docker Compose, Terraform, Ansible
- **Authentication**: Firebase Admin SDK

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Python Version**: ≥3.8
- **ORM**: SQLAlchemy (async)
- **Database Driver**: aiomysql (async), pymysql (sync)
- **Migrations**: Alembic
- **Linting**: Ruff (line-length: 88, tabs for indentation, double quotes)
- **Logging**: python-json-logger

### Frontend
- **Framework**: React 19.1.1
- **Language**: TypeScript ~5.8.3
- **Build Tool**: Vite 7.1.2
- **Styling**: Tailwind CSS 4.1.12
- **Routing**: React Router DOM 7.8.2
- **UI Components**: Radix UI, Lucide React icons

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **IaC**: Terraform
- **Orchestration**: Ansible

---

## Project Structure

```
ticket_resolution_platform/
├── backend/
│   ├── src/ai_ticket_platform/
│   │   ├── core/
│   │   │   ├── clients/          # External service clients (Firebase, Redis, Slack)
│   │   │   ├── logger/           # Logging configuration
│   │   │   └── settings/         # Environment-based settings
│   │   ├── database/
│   │   │   ├── CRUD/             # Database operations (one file per entity)
│   │   │   ├── migrations/       # Alembic migrations
│   │   │   └── main.py           # Database engine initialization
│   │   ├── dependencies/         # FastAPI dependencies (get_db, get_app_settings, etc.)
│   │   ├── routers/              # API route handlers (one file per domain)
│   │   ├── schemas/              # Pydantic models for request/response
│   │   ├── services/             # Business logic services
│   │   └── main.py               # FastAPI application entry point
│   ├── migrations/               # Alembic configuration
│   └── pyproject.toml            # Python dependencies and Ruff config
├── frontend/
│   └── app/
│       └── src/
│           ├── components/       # Reusable React components
│           ├── core/             # Core configuration (Firebase, etc.)
│           ├── hooks/            # Custom React hooks
│           ├── layout/           # Layout components
│           └── pages/            # Page components (route-level)
├── infra/
│   ├── terraform/                # Terraform infrastructure definitions
│   ├── ansible/                  # Ansible playbooks
│   └── scripts/                  # Infrastructure scripts
└── docs/                         # Project documentation
```

---

## Backend Patterns (FastAPI)

### Application Setup

**Pattern**: Use `lifespan` context manager for startup/shutdown events.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_firebase()
    initialize_logger()
    settings.app_settings = settings.initialize_settings()
    clients.redis = clients.initialize_redis_client()
    
    yield
    
    # Shutdown
    logger.debug("INFO: Application shutdown complete.")

app = FastAPI(title="AI Ticket Platform", lifespan=lifespan)
```

**Rules**:
- Always initialize clients in the `lifespan` function
- Use global module-level variables for initialized clients (e.g., `clients.redis`, `settings.app_settings`)
- Never initialize resources in route handlers

### Router Structure

**Pattern**: One router file per domain, all prefixed with `/api`.

```python
from fastapi import APIRouter, Depends, status
from typing import Annotated, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack")  # Domain-specific prefix

@router.post(path="/send-message", status_code=status.HTTP_200_OK)
async def send_message(
    settings: Annotated[object, Depends(get_app_settings)],
    message: str
):
    """Descriptive docstring explaining what the endpoint does."""
    # Implementation
    pass
```

**Rules**:
- All routers are registered in `main.py` with `/api` prefix
- Use `Annotated` type hints for dependencies (FastAPI best practice)
- Always use `status.HTTP_*` constants for status codes
- Include descriptive docstrings for all endpoints
- Use `logger = logging.getLogger(__name__)` in every module
- Handle exceptions with proper error messages and logging

### Router Registration

**Pattern**: Collect routers in a list and iterate to register.

```python
from ai_ticket_platform.routers import health_router, slack_router

routers = [health_router, slack_router]

for router in routers:
    app.include_router(router, prefix="/api")
```

---

## Frontend Patterns (React/TypeScript)

### Component Structure

**Pattern**: Functional components with TypeScript, React Router for navigation.

```typescript
import { Routes, Route } from "react-router-dom"

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Home />} />
        <Route path="/AboutUs" element={<AboutUs />} />
      </Route>
      <Route path="*" element={<p>404 error</p>} />
    </Routes>
  )
}

export default App
```

**Rules**:
- Use functional components only (no class components)
- Export components as default
- Use React Router DOM v7 patterns for routing
- Handle 404s with catch-all route (`path="*"`)

### Custom Hooks

**Pattern**: Extract reusable logic into custom hooks.

```typescript
import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return [user, loading];
};
```

**Rules**:
- Always clean up subscriptions in `useEffect` return
- Return arrays or objects consistently
- Use TypeScript types for all parameters and return values

---

## Configuration Management

### Environment Variables

**Pattern**: Environment-based settings classes with validation.

**Structure**:
1. `Settings` class in `app_settings.py` selects environment-specific settings
2. `BaseSettings` abstract class defines the interface
3. `DevSettings` and `DeploymentSettings` implement environment-specific logic

```python
# app_settings.py
class Settings:
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT").lower()
        if not self.ENVIRONMENT:
            raise ValueError("Environment is not provided. Do export ENVIRONMENT=<value>")
        if self.ENVIRONMENT not in POSSIBLE_ENVIRONMENTS:
            raise ValueError(f"{self.ENVIRONMENT} not an accepted environment")
    
    def get_settings(self):
        return self._extract_all_variables()
    
    def _get_resolve_per_environment(self):
        if self.ENVIRONMENT in ["test", "dev"]:
            return DevSettings()
        elif self.ENVIRONMENT in ["staging", "production"]:
            return DeploymentSettings()
```

**Rules**:
- Always validate `ENVIRONMENT` variable on startup
- Required variables are defined in `required_vars` property
- Use `_extract_*_variables()` methods to group related env vars
- Always call `validate_required_vars()` after extraction

### Environment-Specific Settings

**Dev/Test Pattern**:
```python
class DevSettings(BaseSettings):
    @property
    def required_vars(self):
        return ["REDIS_URL", "MYSQL_USER", "MYSQL_PASSWORD", ...]
    
    def extract_all_variables(self):
        self._extract_database_variables()
        self._extract_app_logic_variables()
```

**Deployment Pattern**:
```python
class DeploymentSettings(BaseSettings):
    def _extract_database_variables(self):
		# Extract variables from environment
		self.MYSQL_HOST = os.getenv("MYSQL_HOST")
```

**Rules**:
- Dev/test: Read credentials directly from environment variables
- Staging/production: Source sensitive credentials from your secure secret store
- Group variable extraction by service (database, app logic, etc.)

### Settings Initialization

**Pattern**: Singleton-like pattern with global variable.

```python
app_settings = None

def initialize_settings():
    global app_settings
    if not app_settings:
        app_settings = Settings().get_settings()
    return app_settings
```

**Rules**:
- Initialize settings once in `lifespan` function
- Use `global` keyword to modify module-level variable
- Access via dependency injection in routes: `Depends(get_app_settings)`

---

## Database Patterns

### Engine Initialization

**Pattern**: Global session factory with connection pooling.

```python
AsyncSessionLocal = None

def initialize_db_engine():
    global AsyncSessionLocal
    if not AsyncSessionLocal:
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,  # Never True in production
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        AsyncSessionLocal = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return AsyncSessionLocal
```

**Rules**:
- Always use async engine (`create_async_engine`)
- Never set `echo=True` in production (performance impact)
- Configure connection pooling appropriately
- Use `pool_pre_ping=True` for connection health checks
- Set `expire_on_commit=False` for async sessions

### Database Dependency

**Pattern**: Yield-based dependency with proper cleanup.

```python
async def get_db() -> AsyncSession:
    AsyncSessionLocal = initialize_db_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Rules**:
- Always use `async with` for session management
- Always close sessions in `finally` block
- Don't commit/rollback in the dependency (do it in route handlers or services)

### CRUD Operations

**Pattern**: One file per entity in `database/CRUD/`.

```python
from sqlalchemy import select, update
from ai_ticket_platform.database import User
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(db: AsyncSession, user_data: CreateUserRequest) -> User:
    db_user = User(...)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def read_user(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def edit_user_name(db: AsyncSession, user_id: str, new_name: str) -> User | None:
    stmt = update(User).where(User.user_id == user_id).values(displayable_name=new_name)
    await db.execute(stmt)
    await db.commit()
    # Fetch updated user
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()
```

**Rules**:
- Use async/await for all database operations
- Always commit after mutations
- Use `scalar_one_or_none()` for single result queries
- Return `None` or raise exceptions for not found cases (be consistent)
- Use SQLAlchemy Core (`select`, `update`) for queries

---

## Client Initialization Patterns

### Client Modules

**Pattern**: Initialize clients in `lifespan`, store as module-level variables.

```python
# clients/__init__.py
redis_client = None

# In lifespan:
clients.redis = clients.initialize_redis_client()
```

**Rules**:
- Initialize clients once during application startup
- Store as module-level variables for global access
- Use singleton-like pattern (check if already initialized)
- Comment out unused client initializations (don't delete)

### Firebase Client

**Pattern**: Support both emulator and production.

```python
def initialize_firebase():
    use_emulator = os.getenv("USING_FIREBASE_EMULATOR")
    if use_emulator:
        firebase_admin.initialize_app(options={"projectId": os.getenv("FB_PROJECT_ID")})
    else:
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
```

**Rules**:
- Always check for existing app before initializing (prevent duplicate initialization)
- Support Firebase Emulator for local development
- Use environment variable to toggle emulator mode

### External Service Clients (Slack, etc.)

**Pattern**: Class-based clients with dependency injection.

```python
class Slack:
    def __init__(self, slack_bot_token: str):
        self.slack_bot_token = slack_bot_token
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "Authorization": f"Bearer {self.slack_bot_token}",
            "Content-Type": "application/json"
        }
    
    def send_channel_message(self, message: str, slack_channel_id: str):
        # Implementation
        pass
```

**Rules**:
- Initialize client instances in route handlers with settings from dependency injection
- Use structured logging in client classes
- Handle errors gracefully and log them

---

## Dependency Injection Patterns

### Settings Dependency

**Pattern**: Async dependency function returning settings.

```python
async def get_app_settings() -> Dict:
    app_settings = initialize_settings()
    return app_settings
```

**Rules**:
- Always use async functions for dependencies (even if not async)
- Access via `Annotated[object, Depends(get_app_settings)]` in route handlers

### Database Dependency

**Pattern**: Session lifecycle managed by FastAPI dependency system.

```python
async def get_db() -> AsyncSession:
    AsyncSessionLocal = initialize_db_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Rules**:
- Use `yield` for dependencies that need cleanup
- Always use type hints: `-> AsyncSession`
- Access via `Annotated[AsyncSession, Depends(get_db)]`

---

## Infrastructure Patterns

### Docker Compose

**Pattern**: Base file + environment-specific overrides.

- `docker-compose.yml`: Base configuration
- `docker-compose.dev.yml`: Development overrides
- `docker-compose.staging.yml`: Staging overrides
- `docker-compose.production.yml`: Production overrides

**Usage**:
```bash
export ENVIRONMENT=dev
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Rules**:
- Always use environment variable `ENVIRONMENT` to determine which override to use
- Use `BACKEND_ENV_FILE` environment variable to pass env file path
- Never hardcode paths or secrets in docker-compose files

### Environment Files

**Pattern**: Synced environment files in `env_config/synced/`.

- Location: `backend/env_config/synced/.env.{ENVIRONMENT}`
- Location: `frontend/env_config/synced/.env.{ENVIRONMENT}`
- Generated by infrastructure scripts from Terraform outputs

**Rules**:
- Never commit `.env.*` files to git
- Use infrastructure scripts to sync env files after Terraform apply
- Each environment has its own set of required variables

### Makefile Usage

**Pattern**: Environment-aware Makefile targets.

**Critical Rules**:
- **Always** set `export ENVIRONMENT={test|dev|staging|production}` before running make targets
- Most targets require environment variable to be set
- Use `check_enviroment_variables` target to validate

**Common Targets**:
- `make install`: Install all project dependencies
- `make dev-start`: Start development environment with hot reload
- `make dev-stop`: Stop development environment
- `make deploy-start`: Deploy infrastructure and application
- `make deploy-stop`: Destroy infrastructure

---

## Code Quality & Standards

### Python (Backend)

**Linting**: Ruff (configured in `pyproject.toml`)
- Line length: 88 characters
- Indentation: Tabs (not spaces)
- Quote style: Double quotes
- Docstring convention: Google style

**Rules**:
- Always run `ruff check` and `ruff format` before committing
- Use type hints for all function parameters and return values
- Use `Annotated` type hints for FastAPI dependencies
- Log errors with `logger.error()` and include exception details
- Use async/await for I/O operations (database, HTTP, etc.)

**Import Organization**:
```python
# Standard library
import os
import logging

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Local application
from ai_ticket_platform.core.clients.slack import Slack
from ai_ticket_platform.dependencies import get_app_settings
```

### TypeScript (Frontend)

**Rules**:
- Use TypeScript strict mode
- Define types/interfaces for all props and state
- Use functional components only
- Use custom hooks for reusable logic
- Handle loading and error states explicitly

### Error Handling

**Backend Pattern**:
```python
try:
    result = some_operation()
    return {"status": "success", "data": result}
except Exception as e:
    logger.error(f"Error description: {str(e)}")
    return {"status": "error", "message": str(e)}
```

**Rules**:
- Always log errors with context
- Return structured error responses (JSON)
- Don't expose internal error details in production responses
- Use appropriate HTTP status codes

---

## Git & PR Conventions

### Commit Message Format

**Pattern**: `type(scope): description`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `infra`: Infrastructure changes
- `docs`: Documentation changes
- `test`: Test additions/changes

**Examples**:
- `feat(frontend): created upload button in upload page`
- `feat(backend): added endpoint to get users`
- `fix(backend): resolved database connection leak`
- `infra(terraform): updated RDS instance type`

**Rules**:
- Commit message becomes PR title
- Use lowercase for type and scope
- Be descriptive but concise
- Scope should match the area (frontend, backend, infra)

### PR Requirements

See `PRAPPROVAL.md` for full requirements. Key points:

1. **Scope & Purpose**: Clear, focused scope
2. **Code Quality**: Consistent formatting, readable code
3. **Tests**: ≥70% coverage for new logic
4. **Backend**: Typed endpoints, proper error handling
5. **Frontend**: No console warnings, proper error handling
6. **Infrastructure**: No hardcoded secrets, tested in staging

**Rules**:
- All PRs must pass CI checks
- Address all reviewer comments before re-requesting review
- Link to related issues/tickets

---

## Development Workflow

### Initial Setup

1. **Set Environment Variable**:
   ```bash
   export ENVIRONMENT=dev  # or test, staging, production
   ```

2. **Install Dependencies**:
   ```bash
   make install  # Root level - installs all
   # Or individually:
   cd backend && make install
   cd frontend && make install
   cd infra && make install
   ```

3. **Set Up Secrets**:
   - Backend Firebase key: `backend/src/ai_ticket_platform/core/clients/secret.*.json`
   - Environment variables: Check `src/settings/environment` for required vars

4. **Start Development**:
   ```bash
   export ENVIRONMENT=dev
   make dev-start
   ```

### Daily Development

1. **Always check environment**:
   ```bash
   echo $ENVIRONMENT  # Should be set
   ```

2. **Run linting before committing**:
   ```bash
   cd backend && ruff check . && ruff format .
   cd frontend && npm run lint
   ```

3. **Stop services cleanly**:
   ```bash
   make dev-stop
   ```

### Adding New Features

1. **Backend**:
   - Create router in `routers/` if new domain
   - Add CRUD operations in `database/CRUD/` if new entity
   - Define schemas in `schemas/endpoints/`
   - Register router in `main.py`
   - Add environment variables if needed

2. **Frontend**:
   - Create page component in `pages/`
   - Create reusable components in `components/`
   - Add route in `App.tsx`
   - Update navigation if needed

3. **Configuration**:
   - Add new env vars to appropriate `*Settings` class
   - Update `required_vars` property
   - Document in README or environment docs

---

## Testing Standards

### Backend Tests

**Tools**: pytest, pytest-asyncio, pytest-mock, httpx

**Pattern**:
- Unit tests for CRUD operations
- Integration tests for API endpoints using FastAPI TestClient
- Mock external services (Firebase, Slack)

**Rules**:
- All new endpoints must have test coverage
- Use `testcontainers` for database testing
- Aim for ≥70% coverage on new code

### Frontend Tests

**Pattern**:
- Component unit tests
- Integration tests for user flows
- Test error and loading states

**Rules**:
- All new components should have tests
- Test user interactions, not implementation details

---

## Key Principles

1. **Environment-First**: Always be aware of which environment you're working in
2. **Dependency Injection**: Use FastAPI's dependency system, don't import globals directly
3. **Async Everywhere**: Use async/await for all I/O operations
4. **Type Safety**: Use type hints in Python, TypeScript types in frontend
5. **Error Handling**: Always handle errors gracefully with logging
6. **Singleton Pattern**: Initialize clients once, reuse globally
7. **Separation of Concerns**: Routers for routes, CRUD for database, Services for business logic
8. **Configuration as Code**: Environment variables drive configuration, not hardcoded values

---

## Common Pitfalls to Avoid

1. **Don't** initialize clients in route handlers (use `lifespan`)
2. **Don't** commit `.env.*` files or secrets
3. **Don't** forget to set `ENVIRONMENT` variable before running commands
4. **Don't** use `echo=True` in production database engine
5. **Don't** forget to close database sessions
6. **Don't** hardcode credentials or paths
7. **Don't** mix sync and async code unnecessarily
8. **Don't** skip error handling or logging
9. **Don't** create PRs without running linters first
10. **Don't** modify dependency files (`dependencies/*.py`) marked with "DONT CHANGE THIS SECTION"

---

## Resources

- **Business Docs**: [Google Drive](https://docs.google.com/document/d/1GDx8ERpdd2Bapt1hQfTBkYGhXiyvSLgq6holw6LnoTM/edit?usp=sharing)
- **Architecture Diagrams**: [Google Drive](https://drive.google.com/drive/folders/1_ayexeN45BHkkeS20wgo95ZOYBF-JX6T?usp=drive_link)
- **PR Approval Guidelines**: See `PRAPPROVAL.md`

---

**Last Updated**: Generated automatically. Review and update this document when patterns change.

