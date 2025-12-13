# Manager Instructions for Claude Code

## Core Constraints (DO NOT CHANGE)

These constraints apply to ALL work unless explicitly discussed and approved:

### 1. Virtual Environments
- ❌ DO NOT modify virtual environment setup
- ❌ DO NOT change venv activation scripts
- ❌ DO NOT remove/add dependencies directly to venv
- ✅ Dependencies can be added to `pyproject.toml` under `[project.optional-dependencies]`

### 2. Makefile
- ❌ DO NOT modify existing Makefile targets
- ✅ ONLY add new targets (don't change existing ones)
- ✅ New targets should follow existing naming conventions
- Example: Can add `test-smoke` but cannot modify `test-integration`

### 3. Environment Variables & Configuration
- ❌ DO NOT modify existing environment variable handling code
- ❌ DO NOT change how settings classes load env vars
- ❌ DO NOT modify existing `.env.*` files (dev, staging, production)
- ✅ CAN create new `.env.*` files (e.g., `.env.test`)
- ✅ CAN add new environment variables to `.env.test`
- ✅ CAN override env vars in docker-compose files for specific services

## Docker & Testing Setup

### Port Mappings (Important!)
- **Host access:** Use mapped ports (e.g., `127.0.0.1:3307`)
- **Container access:** Use internal ports (e.g., `database:3306`)
- Override `MYSQL_PORT` in docker-compose to `3306` for containers, `3307` for host

### Environment Setup for Tests
- Always set `ENVIRONMENT=test` when running test targets
- Use `.env.test` for test configuration
- `.env.test` should NOT be committed (it's gitignored)

### Test Hierarchy
1. **Smoke Tests** - Verify Docker services are accessible (lightweight)
2. **Unit Tests** - Test individual functions (70% coverage minimum)
3. **Integration Tests** - Test real MySQL/Redis with actual code paths
4. **E2E Tests** - Test complete user workflows

## Code Quality Standards

### Commits
- Use conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `refactor`, `infra`, `docs`, `test`
- ❌ DO NOT include Claude Code attribution or collaboration markers
- ❌ DO NOT include "Generated with Claude Code" footers
- Example: `feat(ci): Add Docker-based smoke tests for service verification`

### Testing Requirements
- ✅ 70% coverage minimum for new unit test code
- ✅ All new endpoints must have tests
- ✅ Smoke tests don't need high coverage (they're verification, not code coverage)
- ✅ Integration tests should use real databases (MySQL, Redis)

### Code Style
- Follow existing project conventions in CLAUDE.md
- Use ruff for Python formatting
- Type hints required for all functions
- Async/await for I/O operations

## Git Workflow

### Branching
- Create feature branches for new work
- Naming: `feat/description` or `fix/description`
- Keep branches focused on single feature/fix

### Pull Requests
- Write clear commit messages following conventional format
- Include what changed and why
- Link to related issues/tickets if applicable
- NO collaboration markers or attribution in commits

### Before Pushing
1. Run tests locally and ensure they pass
2. Check coverage meets requirements (70% for unit tests)
3. Remove any Claude Code/collaboration markers
4. Verify commits follow conventional format

## Common Patterns

### Adding Tests
1. Create test file in appropriate directory
2. Follow existing test patterns
3. Use fixtures from conftest.py
4. Ensure 70% coverage for unit tests (not required for smoke tests)

### Adding Makefile Targets
```makefile
test-smoke: ## Run smoke tests for Docker service verification
	@echo "$(YELLOW)Running smoke tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv tests/smoke/
```

### Docker Configuration
- Use docker-compose.test.yml for test-specific overrides
- Override internal ports for containers (3306 for MySQL)
- Keep host mappings (3307:3306) consistent
- Always set `ENVIRONMENT=test` when using test docker-compose

## Important Notes

- Always check `CLAUDE.md` in the project root for architecture patterns
- Follow the testing pyramid: many unit tests, fewer integration tests, even fewer E2E tests
- Test environment variables are NOT production secrets (they're test values)
- Smoke tests verify infrastructure, not code coverage
- Integration tests need real services (MySQL, Redis) running

## Questions or Clarifications?

If anything is unclear about these constraints, ask before proceeding. These rules exist to maintain code quality and consistency.

---

**Last Updated:** November 27, 2025
**Status:** Active - Reference when needed for future sessions
