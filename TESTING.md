# Testing Guide

## Running Tests Without Docker

The test suite automatically detects if PostgreSQL is available and falls back to SQLite in-memory for testing.

### Quick Start (No Docker Required)

```bash
cd apps/api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run tests (will use SQLite automatically if no Postgres)
pytest
```

### With Docker (Full Integration)

```bash
# Start only the database
docker compose up -d db redis

# Run tests against real Postgres
cd apps/api
pytest
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_DATABASE_URL` | auto-detect | Force specific database URL |
| `DATABASE_URL` | postgres://...localhost:5432 | Used if Postgres is available |

### Test Structure

```
tests/
├── conftest.py          # Fixtures, DB setup
├── test_health.py       # Basic health checks
├── test_auth_flow.py    # Authentication tests
├── test_tenant_isolation.py  # Multi-tenant security
├── test_inventory.py    # Inventory CRUD
├── test_locations.py    # Locations CRUD
├── test_orders.py       # Orders CRUD
├── test_picker.py       # Picking workflow
├── test_audit.py        # Audit logging
├── test_sync.py         # Sync engine
└── test_webhooks.py     # Webhooks
```

### Known Limitations with SQLite

When running with SQLite (no Docker):
- Some PostgreSQL-specific features are mocked
- UUID fields use CHAR(36) instead of native UUID
- JSONB uses standard JSON
- ARRAY fields use JSON arrays
- Full-text search not available

For production-like testing, always use PostgreSQL.

### Running Specific Tests

```bash
# Single file
pytest tests/test_auth_flow.py

# Single test
pytest tests/test_auth_flow.py::test_login_creates_session

# With coverage
pytest --cov=app --cov-report=html
```

### Debugging Test Failures

```bash
# Verbose output
pytest -vvv

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```
