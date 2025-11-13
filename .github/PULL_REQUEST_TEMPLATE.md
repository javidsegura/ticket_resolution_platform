# Pull Request Template

## Summary
- [ ] PR title follows `<type(scope): summary>` format (e.g. `feat(frontend): add upload button`).
- [ ] Purpose is clearly stated (feature, fix, refactor, infra, etc.).
- [ ] Scope is focused; no unrelated or excessive changes.

**Context / Issue Link**
- Related ticket(s) or concise context for reviewers:

## Changes
- Provide a brief, reviewer-friendly list of the main changes:

## Impacted Areas
- [ ] Backend (FastAPI)
- [ ] Frontend (React)
- [ ] Infrastructure / DevOps
- [ ] Other: 

> Complete the relevant checklists below for each checked area.

## Trunk-Based Readiness
- [ ] Branch created from the latest `main` and rebased before merge.
- [ ] Change set is small, incremental, and production-ready.
- [ ] Feature flags or safe defaults guard incomplete functionality.
- [ ] Commit history is clean (single commit or squash-ready).
- [ ] No pending follow-up work required to keep `main` stable.

## Global Code Quality
- [ ] Code uses meaningful names and remains readable.
- [ ] Formatting, linting, and style rules match the project standards.
- [ ] Functions/components remain small, cohesive, and easy to test.
- [ ] No obvious security issues (XSS, SQL injection, unsafe operations).
- [ ] No unnecessary loops, API calls, or expensive computations.

## Testing
- [ ] Added or updated unit/integration tests for new logic.
- [ ] Tests are deterministic, readable, and relevant.
- [ ] Overall coverage ≥ 70% or meets the project baseline.
- [ ] CI pipeline completed successfully with all tests green.
- [ ] New FastAPI endpoints covered by test client specs (if applicable).
- [ ] New React components covered by unit tests (if applicable).
- [ ] Built app or service verified locally/staging (if applicable).

## Backend (FastAPI)
- [ ] Endpoints use typed params and Pydantic models.
- [ ] Input/output validation is complete.
- [ ] Proper error handling with `HTTPException` and relevant status codes.
- [ ] FastAPI test client exercises new or modified routes.

## Frontend (React)
- [ ] Component and file structure follow project conventions.
- [ ] Hooks/context/state are used appropriately (no unnecessary prop drilling).
- [ ] Loading and error states handled gracefully.
- [ ] No console warnings or runtime errors.
- [ ] Built app runs without breaking existing functionality.

## Infrastructure / DevOps
- [ ] Dockerfile builds cleanly and reproducibly; no secrets committed.
- [ ] Environment variables added to `.env.example`.
- [ ] CI/CD pipelines updated/passing where applicable.
- [ ] Infra changes tested locally or in staging.
- [ ] No unnecessary or vulnerable dependencies introduced.

## Additional Notes
- Optional screenshots, videos, or logs to help reviewers:

## PR AI Reviewers
- [ ] All Gemini comments are resolved.


