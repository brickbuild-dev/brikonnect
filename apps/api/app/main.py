from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
import sentry_sdk

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, log
from app.db.session import AsyncSessionLocal
from app.middleware.logging import add_correlation_id
from app.middleware.rate_limit import limiter

configure_logging()

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.BRIKONNECT_ENV,
    )

app = FastAPI(
    title="Brikonnect API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    return await add_correlation_id(request, call_next)

@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"ok": True, "service": "brikonnect-api"}


@app.get("/ready", tags=["ops"])
async def ready() -> dict:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"ok": True, "database": "ready"}

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
