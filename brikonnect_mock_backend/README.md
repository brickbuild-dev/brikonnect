# brikonnect-mock-backend (FastAPI)

This is a **mock** backend generated from HAR traffic captured on `demo.brikonnect.com`.

## What you get
- `openapi.yaml`: inferred OpenAPI 3.0 spec.
- `main.py`: FastAPI app that returns captured example payloads when available.
- Login sets a `sessionid` cookie (mocked).

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

API should be at:
- http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Notes
- Endpoints returning `text/html` are implemented explicitly:
  - `POST /api/v1/orders/receipt-settings/preview/`
  - `POST /api/v1/orders/notification-template/{id}/preview/`
- Many endpoints in the HAR did not include response bodies; those return a generic stub.
- This is not production code; it is a scaffolding to wire the UI and iterate.

