"""
FIFA World Cup 2026 Stadium Operations Core Application Entry Point.

Initializes FastAPI application, security middleware headers, sliding-window rate limiting,
Prometheus metrics, Sentry error tracking, global exception handlers, and API routers.
"""
from collections import defaultdict
from contextlib import asynccontextmanager
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.crowd import router as crowd_router
from app.api.decision import router as decision_router
from app.api.match import router as match_router
from app.api.sustainability import router as sustainability_router
from app.api.transport import router as transport_router
from app.api.ws import router as ws_router
from app.core.config import settings
from app.core.constants import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from app.core.exceptions import (
    global_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger
from app.database import init_db

load_dotenv()

# ─── Sentry Error Tracking ───────────────────────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )


# ─── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "fifa_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "fifa_http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


# ─── Lifespan Context Manager ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Lifespan event handler for startup and shutdown lifecycle management."""
    init_db()
    logger.info("FIFA WC 2026 Operations DB initialized successfully.")
    yield


# ─── Rate Limiter (Redis-backed if available, in-memory fallback) ─────────────
RATE_LIMIT_WINDOW = RATE_LIMIT_WINDOW_SECONDS
RATE_LIMIT_MAX_REQUESTS = RATE_LIMIT_MAX_REQUESTS

try:
    import redis as redis_lib

    REDIS_URL = os.environ.get("REDIS_URL", "")
    _redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
    if _redis_client:
        _redis_client.ping()
except Exception:
    _redis_client = None

_memory_tracker: dict = defaultdict(list)


def _check_rate_limit(client_ip: str) -> bool:
    """Returns True if the request is allowed, False if rate-limited."""
    if _redis_client:
        key = f"ratelimit:{client_ip}"
        current = _redis_client.get(key)
        count = int(current) if current else 0
        if count >= RATE_LIMIT_MAX_REQUESTS:
            return False
        pipe = _redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, RATE_LIMIT_WINDOW)
        pipe.execute()
        return True
    else:
        # In-memory fallback
        now = time.time()
        _memory_tracker[client_ip] = [
            t for t in _memory_tracker[client_ip] if now - t < RATE_LIMIT_WINDOW
        ]
        if len(_memory_tracker[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        _memory_tracker[client_ip].append(now)
        return True


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="FIFA World Cup 2026 Stadium Operations Core",
    description="GenAI-Enabled Venues Operations and Safety Coordination API Services.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── Security Headers Middleware ──────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware injecting OWASP security headers into all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        """Process HTTP request and attach security headers.

        Args:
            request: Incoming HTTP Request instance.
            call_next: Middleware call_next handler.

        Returns:
            HTTP Response with security headers.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "connect-src 'self' ws://localhost:8000 wss://localhost:8000; "
            "img-src 'self' data:;"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"
        return response


# ─── Rate Limiting Middleware ─────────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing sliding-window rate limiting on API endpoints."""

    async def dispatch(self, request: Request, call_next):
        """Check client rate limits and block requests exceeding threshold.

        Args:
            request: Incoming HTTP Request instance.
            call_next: Middleware call_next handler.

        Returns:
            HTTP Response or 429 Too Many Requests JSONResponse.
        """
        if request.url.path in ["/metrics", "/ws/updates"] or request.url.path.startswith("/ws"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if not _check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down and try again later."},
            )
        return await call_next(request)


# ─── Observability Middleware ─────────────────────────────────────────────────
class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware tracking request latency and counter metrics for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        """Record latency and request count Prometheus metrics.

        Args:
            request: Incoming HTTP Request instance.
            call_next: Middleware call_next handler.

        Returns:
            HTTP Response instance.
        """
        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time

        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(latency)

        return response


# ─── Register Middlewares (order matters — last added is first executed) ──────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ─── Prometheus metrics endpoint ──────────────────────────────────────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ─── Global Exception Handlers ───────────────────────────────────────────────
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ─── API Routers ──────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["Assistant"])
app.include_router(crowd_router, prefix="/api/crowd", tags=["Crowd"])
app.include_router(transport_router, prefix="/api/transport", tags=["Transport"])
app.include_router(sustainability_router, prefix="/api/sustainability", tags=["Sustainability"])
app.include_router(decision_router, prefix="/api/decision", tags=["Decision"])
app.include_router(match_router, prefix="/api/match", tags=["Match"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
def read_root() -> dict[str, str]:
    """Return platform API root status."""
    return {
        "status": "online",
        "system": "FIFA WC 2026 Stadium Operations Core",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return detailed platform component health status."""
    return {"status": "healthy", "redis": "connected" if _redis_client else "in-memory fallback"}
