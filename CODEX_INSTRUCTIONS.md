# Instructions for Codex Agent

## Current Status

The M1-M6 implementation is complete. Now implementing additional features from `PROMPT_BRIKONNECT_V3_NEXT_STEPS.md`.

## Environment Limitations

This environment does NOT have:
- Docker
- PostgreSQL running locally
- Redis running locally

## How to Run Tests

Tests are configured to **automatically use SQLite** when PostgreSQL is not available.

```bash
cd apps/api
pip install -r requirements-dev.txt
pytest -v
```

The `conftest.py` has been updated to detect if Postgres is available and fallback to SQLite.

## Files Available

- `PROMPT_BRIKONNECT_V2.md` — Original implementation spec (M1-M6) ✅ DONE
- `PROMPT_BRIKONNECT_V3_NEXT_STEPS.md` — Next features to implement
- `TESTING.md` — How to run tests without Docker

## Implementation Order

Follow `PROMPT_BRIKONNECT_V3_NEXT_STEPS.md` in this order:

1. **FASE 1: Billing System** (Priority: High)
   - Create migration `0007_billing.py`
   - Create module `app/modules/billing/`
   - Implement GMV calculation, invoices, payments
   - Add Stripe and PayPal stubs

2. **FASE 2: Catalog Cache** (Priority: Medium)
   - Create migration `0008_catalog.py`
   - Create module `app/modules/catalog/`
   - Multi-reference search

3. **FASE 3: Brickognize** (Priority: Medium)
   - Create migration `0009_brickognize.py`
   - Create module `app/modules/brickognize/`

4. **FASE 4: Shipping Carriers** (Priority: Medium)
   - Expand `app/integrations/shipping/`

5. **FASE 5: Email System** (Priority: Medium)
   - Create migration `0010_email.py`
   - Create module `app/modules/email/`

6. **FASE 6: Polish** (Priority: High before launch)
   - Dark mode toggle
   - Error handling
   - CI/CD

## How to Create a Migration

```bash
cd apps/api

# Create migration file manually in alembic/versions/
# Name format: 0007_description.py

# The migration should:
# 1. Import from alembic import op
# 2. Import sqlalchemy as sa
# 3. Define upgrade() and downgrade() functions
```

## Testing Your Changes

After implementing each module:

```bash
cd apps/api
pytest tests/test_<module>.py -v
```

Create new test files as needed in `tests/`.

## Commits

Make incremental commits after each sub-feature:

```bash
git add .
git commit -m "FASE 1: Add billing models and migration"
git push
```

## Questions?

If you encounter issues:
1. Check if it's a PostgreSQL-specific feature → use compatibility types from `app/db/types.py`
2. Check if test needs real DB → mock the database calls
3. Check if external API needed → create stub/mock

Proceed with FASE 1 (Billing System).
