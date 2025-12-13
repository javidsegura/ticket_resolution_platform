![Coverage](https://img.shields.io/badge/coverage-71%25-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![React](https://img.shields.io/badge/frontend-react%4019.1.1-blue)
![Azure](https://img.shields.io/badge/cloud-azure-blue)
![AI-Powered](https://img.shields.io/badge/AI-LLM%20Powered-purple)
![Testing](https://img.shields.io/badge/testing-pytest%20%7C%20playwright-green)

# AI-Powered Ticket Resolution Platform

A production-ready intelligent ticket resolution system built with FastAPI and React, featuring AI-powered clustering, automated content generation, and comprehensive CI/CD automation.

## Overview

This platform provides an AI-driven solution for automatically clustering, categorizing, and resolving customer support tickets using LLM-based intent matching, hierarchical categorization, automated knowledge base generation, and company document RAG (Retrieval Augmented Generation).

### Key Features

**Core Functionality**
- FastAPI backend with async/await patterns
- React 19 + TypeScript frontend
- AI-powered ticket clustering with LLM intent matching
- Hierarchical 3-level category taxonomy (L1/L2/L3)
- Automated article generation using LangGraph workflows
- Company document RAG with ChromaDB vector search
- Queue-based background processing with Redis Queue (RQ)
- Firebase authentication integration

**DevOps & Infrastructure**
- Complete CI/CD pipeline with 6-stage testing
- 71% test coverage with 508+ unit tests
- Infrastructure as Code with Terraform and Ansible
- Docker Compose orchestration
- Azure cloud deployment

### Architecture Diagrams

**System Architecture Overview**
```mermaid
graph TB
    subgraph "Frontend Layer"
        React[React 19 App<br/>TypeScript + Vite]
        UI[Modern UI<br/>Radix + Tailwind]
    end

    subgraph "API Gateway"
        Nginx[Nginx Reverse Proxy<br/>Port 80/443]
    end

    subgraph "Backend Services"
        FastAPI[FastAPI Application<br/>Async/Await + Uvicorn]

        subgraph "Core Services"
            Clustering[Ticket Clustering Service<br/>LLM Intent Matching]
            ArticleGen[Article Generation Service<br/>LangGraph Workflows]
            DocProc[Document Processing Service<br/>PDF + ChromaDB]
        end

        subgraph "Background Jobs"
            RQ[Redis Queue Workers<br/>Async Job Processing]
        end
    end

    subgraph "Data Layer"
        MySQL[(MySQL 8.0<br/>Async SQLAlchemy)]
        Redis[(Redis 7<br/>Cache + Queue)]
        ChromaDB[(ChromaDB<br/>Vector Store)]
        AzureBlob[Azure Blob Storage<br/>Document Files]
    end

    subgraph "External Services"
        Firebase[Firebase<br/>Authentication]
        OpenRouter[OpenRouter API<br/>LLM Gateway]
    end

    React --> Nginx
    UI --> Nginx
    Nginx --> FastAPI

    FastAPI --> Clustering
    FastAPI --> ArticleGen
    FastAPI --> DocProc
    FastAPI --> RQ

    Clustering --> MySQL
    ArticleGen --> MySQL
    DocProc --> MySQL

    RQ --> MySQL
    RQ --> Redis

    FastAPI --> Redis
    DocProc --> ChromaDB
    DocProc --> AzureBlob

    FastAPI --> Firebase
    Clustering --> OpenRouter
    ArticleGen --> OpenRouter
    DocProc --> OpenRouter

    style React fill:#61DAFB
    style FastAPI fill:#009688
    style MySQL fill:#4479A1
    style Redis fill:#DC382D
    style ChromaDB fill:#FF6F00
    style Firebase fill:#FFCA28
    style OpenRouter fill:#7C4DFF
```

**Continuous Integration Pipeline**
```mermaid
flowchart TB
    A1[Push to branch] --> B1[Stage 1: Lint & Security]

    B1 --> C1[Ruff Format Check<br/>Ruff Lint Check<br/>Bandit Security Scan]
    C1 -->|✓ Pass| D1[Stage 2: Unit Tests]
    C1 -->|✗ Fail| FAIL[Block merge ✗]

    D1 --> E1[Pytest Unit Tests<br/>508+ tests<br/>71% coverage minimum]
    E1 -->|✓ Pass| F1{PR to main?}
    E1 -->|✗ Fail| FAIL

    F1 -->|No| SUCCESS[Complete ✓]
    F1 -->|Yes| G1[Stage 3: Smoke Tests]

    G1 --> H1[Docker Compose Up<br/>Service Health Checks<br/>Basic API Tests]
    H1 -->|✓ Pass| I1[Stage 4: Integration Tests]
    H1 -->|✗ Fail| FAIL

    I1 --> J1[Real Services<br/>MySQL + Redis + ChromaDB<br/>Full Workflow Tests]
    J1 -->|✓ Pass| K1[Stage 5: Regression Tests]
    J1 -->|✗ Fail| FAIL

    K1 --> L1[Historical Bug Tests<br/>Edge Cases<br/>Race Conditions]
    L1 -->|✓ Pass| M1[Stage 6: E2E Tests]
    L1 -->|✗ Fail| FAIL

    M1 --> N1[Playwright Browser Tests<br/>Full User Journeys<br/>UI Validation]
    N1 -->|✓ Pass| SUCCESS
    N1 -->|✗ Fail| FAIL

    style FAIL fill:#f8d7da
    style SUCCESS fill:#d4edda
    style B1 fill:#fff3cd
    style D1 fill:#cfe2ff
    style G1 fill:#d1e7dd
    style I1 fill:#e1f5ff
    style K1 fill:#fff4e1
    style M1 fill:#d4edda
```

**Ticket Processing Workflow**
```mermaid
flowchart LR
    subgraph "Ingestion"
        CSV[CSV Upload] --> Queue1[RQ Job Queue]
        API[API Create] --> Queue1
    end

    subgraph "Stage 1: Clustering"
        Queue1 --> Batch[Batch Processor]
        Batch --> LLM1[LLM Intent Matcher]
        LLM1 --> Decision{Match or Create?}

        Decision -->|Match| Match[Update ticket_intent<br/>Reuse category]
        Decision -->|Create| Create[Create new intent<br/>Create L1/L2/L3 categories]
    end

    subgraph "Stage 2: Article Generation"
        Match --> Queue2[Article Gen Queue]
        Create --> Queue2

        Queue2 --> Check{Article exists<br/>for intent?}
        Check -->|No| Generate[LangGraph Workflow<br/>Generate article]
        Check -->|Yes| Skip[Skip generation]

        Generate --> Review[Article Review<br/>Status: pending]
    end

    subgraph "Stage 3: RAG Enhancement"
        Review --> Approve{Approved?}
        Approve -->|Yes| Index[Index to ChromaDB<br/>Create embeddings]
        Approve -->|No| Iterate[Iteration requested]

        Iterate --> Regenerate[Regenerate article]
        Regenerate --> Review
    end

    Index --> Done[Available for<br/>ticket resolution]

    style CSV fill:#4CAF50
    style LLM1 fill:#9C27B0
    style Generate fill:#FF9800
    style Index fill:#2196F3
```

**Azure Production Architecture**
```mermaid
graph TB
    subgraph "Azure Production Environment"
        VNet[Virtual Network<br/>10.0.0.0/16]

        subgraph "Public Subnet<br/>10.0.1.0/24"
            VM[Application VM<br/>Docker Compose Stack]
            PIP[Public IP<br/>SSH: 22, HTTP: 80, HTTPS: 443]
        end

        subgraph "Private Subnet<br/>10.0.2.0/24"
            MySQL[(MySQL Flexible Server<br/>ai_ticket_platform DB)]
        end

        subgraph "Container Services"
            Backend[Backend Container<br/>FastAPI + Uvicorn]
            Frontend[Frontend Container<br/>Nginx + React Build]
            Redis[Redis Container<br/>Cache + Queue]
            ChromaDB[ChromaDB Container<br/>Vector Store]
            Worker[RQ Worker Container<br/>Background Jobs]
        end

        NSG[Network Security Group<br/>Ports: 22, 80, 443, 3000, 6379]
        KV[Azure Key Vault<br/>DB Credentials + API Keys]
        Blob[Azure Blob Storage<br/>Company Documents]
    end

    subgraph "External Services"
        Firebase[Firebase Auth]
        OpenRouter[OpenRouter LLM API]
    end

    subgraph "Terraform State"
        StateBlob[(Azure Storage<br/>tfstate files)]
    end

    VNet --> VM
    VNet --> MySQL
    NSG --> VM
    PIP --> VM

    VM --> Backend
    VM --> Frontend
    VM --> Redis
    VM --> ChromaDB
    VM --> Worker

    Backend --> MySQL
    Worker --> MySQL
    Backend --> Redis
    Worker --> Redis
    Worker --> ChromaDB

    Backend -.->|Reads secrets| KV
    Worker -.->|Uploads PDFs| Blob

    Backend --> Firebase
    Backend --> OpenRouter
    Worker --> OpenRouter

    StateBlob -.->|State locking| VNet

    style VM fill:#4CAF50
    style MySQL fill:#2196F3
    style KV fill:#FF9800
    style Blob fill:#9C27B0
    style Backend fill:#00BCD4
    style Worker fill:#FFC107
```

**Additional Architecture Resources**
- [Business Documentation](https://docs.google.com/document/d/1GDx8ERpdd2Bapt1hQfTBkYGhXiyvSLgq6holw6LnoTM/edit?usp=sharing)
- [Architecture Diagrams](https://drive.google.com/drive/folders/1_ayexeN45BHkkeS20wgo95ZOYBF-JX6T?usp=drive_link)

## See Extended Documentation
[CLAUDE.md](CLAUDE.md) - Comprehensive coding standards, architectural patterns, and development guidelines

---

## Prerequisites

- Python 3.8+ (Python 3.11 recommended)
- Docker and Docker Compose
- Node.js 18+ and npm
- Terraform (for infrastructure deployment)
- Ansible (for configuration management)
- AWS or Azure account (for production deployment)

---

## HOW TO RUN DEVELOPMENT

### Credentials

You need to setup environment variables for both frontend and backend folders.

#### Backend

Create file: `/backend/env_config/synced/.env.dev`

Include:

```bash
ENVIRONMENT="dev"
REDIS_URL="redis://redis:6379"
MYSQL_USER="root"
MYSQL_PASSWORD="rootpassword"
MYSQL_HOST="database"
MYSQL_PORT=3306
MYSQL_DATABASE="ai_ticket_platform"
MYSQL_SYNC_DRIVER="mysql+pymysql"
MYSQL_ASYNC_DRIVER="mysql+aiomysql"
SLACK_WEBHOOK_URL=
GF_SECURITY_ADMIN_PASSWORD=admin
CLOUD_PROVIDER='aws'
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_MAIN_REGION=us-east-1
## TERRAFORM OUTPUTS:
S3_MAIN_BUCKET_NAME=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=company-docs
```

#### Frontend

Create file: `frontend/app/env_config/synced/.env.dev`

Include:

```bash
apiKey=
authDomain=
projectId=
storageBucket=p
messagingSenderId=
appId=
measurementId=
VITE_BASE_URL=http://localhost/api/
```

### Install Dependencies

Run from root:

```bash
make install
```

### Set Environment to Dev

Run from root:

```bash
export ENVIRONMENT=dev
```

### Run Dev

Run from root:

```bash
make dev-start
```

**Access services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost/api
- Backend Docs: http://localhost/api/docs

**Stop development environment:**

```bash
make dev-stop
```

---

## HOW TO RUN PRODUCTION

### Credentials

You need admin-level credentials.

For that you need to set up your AWS access key ID or AWS secret key (you need to create them). You can use environment variables or write them locally in your computer (best practice). For the latter, see the following code snippet:

```bash
~/.aws/credentials
```

**File contents:**

```ini
[default]
aws_access_key_id = ""
aws_secret_access_key = ""
```

### Set the Proper Environment Variables

```bash
export ENVIRONMENT="production"  # or "staging"
export CLOUD_PROVIDER="aws"      # or "azure"
export BACKEND_VERSION="v0.0.1"  # for example: v0.0.1
```

### Go to `./infra`

```bash
cd infra
```

### Run Remote State Initialization

Run `make start-remote-state`, copy the S3 bucket name of the remote state.

```bash
make start-remote-state
```

### Configure Backend for Remote State

Go into `./infra/terraform{CLOUD_PROVIDER}/environment/{ENVIRONMENT}/main.tf` and change the backend configuration to reflect the remote state S3 bucket name captured in the prior step.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket  = "ai-ticket-platform-remote-state-bucket-zxmluk37" # Change
    key     = "remote-state/dev/terraform.tfstate"               # Keep
    region  = "us-east-1"                                         # Change if needed
    encrypt = true                                                # Keep
  }
}
```

### Run Install

```bash
make install
```

### Configure Terraform Variables

Go to `./infra/terraform{CLOUD_PROVIDER}/environment/{ENVIRONMENT}/terraform.tfvars` and write:

```hcl
environment   = "production"
main_region   = "us-east-1"
db_username   = "root"
project_name  = "ai_ticket_platform"
```

### Deploy to Production

Go back to the root and run either:

```bash
make deploy-start-artifacts  # Deploy to production (process: build artifacts + ansible)
make deploy-start-ansible    # Deploy to production (process: ansible)
make deploy-start-infra      # Deploy to production (process: infra + build artifacts + ansible)
make deploy-stop-infra       # Stop development environment
```

---

## Running Tests

### Backend Tests

```bash
cd backend

# Start test infrastructure (MySQL, Redis, ChromaDB with test configs)
make test-start

# Run specific test categories
make unit-test          # Unit tests only (71% coverage target)
make integration-test   # Integration tests with real services
make regression-test    # Regression tests for historical bugs
make smoke-test         # Smoke tests for health checks
make load-tests         # Load tests with k6

# Stop test infrastructure
make test-stop
```

### Frontend Tests

```bash
cd frontend/app

# Run linting
npm run lint

# Run format check
npm run format:check

# Fix formatting
npm run format
```

### End-to-End Tests

```bash
cd backend
make e2e-test  # Runs Playwright browser automation tests
```

---

## Tech Stack

### Backend
- Python (>=3.8), FastAPI, Uvicorn, Gunicorn
- Pydantic, SQLAlchemy (async ORM), MySQL 8.0, Alembic
- Redis 7 (caching + queue), RQ (background jobs)
- Firebase Admin, LangChain, LangGraph, ChromaDB, PDFPlumber
- Azure SDK (Blob Storage, Key Vault), Boto3 (AWS SDK)
- Prometheus FastAPI Instrumentator

### Frontend
- React (19.1.1), TypeScript (~5.8.3), Vite (7.1.2)
- React Router DOM (7.8.2), Tailwind CSS (4.1.12)
- Firebase (12.2.0), Radix UI, Lucide React
- React Hot Toast, React Markdown

### Infrastructure & DevOps
- Docker & Docker Compose, Nginx
- Terraform, Ansible, Azure

### Testing Tools
- Pytest, Pytest-asyncio, Playwright, k6
- ESLint, Prettier, Ruff, Bandit, Pre-commit

### AI Services
- OpenRouter (LLM API gateway)
- Google Gemini (via LangChain)
- ChromaDB (vector embeddings)

---

## References

- [Business Documentation](https://docs.google.com/document/d/1GDx8ERpdd2Bapt1hQfTBkYGhXiyvSLgq6holw6LnoTM/edit?usp=sharing)
- [Architecture Diagrams](https://drive.google.com/drive/folders/1_ayexeN45BHkkeS20wgo95ZOYBF-JX6T?usp=drive_link)
- [Coding Standards](CLAUDE.md)
- [PR Approval Guidelines](PRAPPROVAL.md)

---

## License

MIT License
