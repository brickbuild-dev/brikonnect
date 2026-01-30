from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, log
from app.api.v1.router import api_router

configure_logging()

app = FastAPI(
    title="Brikonnect API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)

# CORS (dev + controlled production)
origins = [o.strip() for o in settings.BRIKONNECT_ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"ok": True, "service": "brikonnect-api"}

@app.middleware("http")
async def request_logging(request: Request, call_next):
    response = await call_next(request)
    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    )
    return response

app.include_router(api_router, prefix="/api/v1")
