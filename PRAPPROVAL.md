## Overview
For a Pull Request (PR) to be approved by a member of the team, the user must specify in their PR (commit message) the type of PR and fulfill all of the requirements of such type.

The commit message you write on your commit will be the title of your PR.

Why this format? It’s not the only format out there, but It’s very convenient for commit messages to have this format since the reviewer or LLM will immediately be able to know what the PR is about and what to look for, and also to spot bugs faster.

Examples of commit messages: 
- _“feat(frontend): created an upload button in upload page”_
- _“feat(backend): added endpoint to get users”_
- _“feat(infra): changed the config for k8s”_


## Conditions
###Global Scope & Purpose
- The PR clearly states its purpose (feature, fix, refactor, infra, etc.).
- Scope is focused; no unrelated or excessive changes.
- Links to issue/ticket or includes concise context for reviewers.

###Code Quality
- Code is readable and uses meaningful naming conventions.
- Consistent with existing formatting, linting, and style rules.
- Functions and components are small, cohesive, and easy to test.
- No obvious security issues (XSS, SQL injection, unsafe operations).
- No unnecessary loops, API calls, or expensive UI/backend computations.

###Tests (Backend)
- All new logic is covered by FastAPI and frontend unit tests.
- Overall test coverage is ≥ 70% or meets current project baseline.
- Tests are deterministic, readable, and relevant.
- CI passes successfully with all tests green.

###Backend (FastAPI)
- Endpoints follow FastAPI best practices with typed params and Pydantic models.
- Input/output validation is implemented.
- Proper error handling with HTTPException and relevant status codes.
- Includes FastAPI test client coverage for all new or modified routes.

###Frontend (React)
- Component and file structure follow project conventions.
- Proper use of hooks/context/state management (no prop drilling abuse).
- Errors and loading states are handled gracefully.
- No console warnings or runtime errors.
- Built app runs without breaking existing functionality.

###Infrastructure / DevOps
- Dockerfile builds cleanly and reproducibly; no secrets hardcoded.
- Environment variables are declared in .env.example.
- CI/CD pipelines pass successfully.
- Infra changes (Docker Compose, Terraform, etc.) are tested locally or in staging.
- No unnecessary or vulnerable dependencies added.

### PR AI Reviewers
- You need to resolve all of Gemini or reviewer comments before asking for another review.
