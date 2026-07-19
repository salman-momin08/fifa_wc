import os
import time
import json
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.database import init_db
from app.api.auth import router as auth_router
from app.api.assistant import router as assistant_router
from app.api.crowd import router as crowd_router
from app.api.transport import router as transport_router
from app.api.sustainability import router as sustainability_router
from app.api.decision import router as decision_router
from app.api.ws import router as ws_router

# ─── Sentry Error Tracking ───────────────────────────────────────────────────
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,  # Ensures PII is NOT sent to Sentry
    )

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "fifa_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "fifa_http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# ─── Rate Limiter (Redis-backed if available, in-memory fallback) ─────────────
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 60

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
    redoc_url="/redoc"
)

# ─── Security Headers Middleware ──────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
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
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting on WebSocket handshakes and metrics endpoints
        if request.url.path in ["/metrics", "/ws/updates"] or request.url.path.startswith("/ws"):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        if not _check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down and try again later."}
            )
        return await call_next(request)

# ─── Observability Middleware ─────────────────────────────────────────────────
class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time
        
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)
        
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

# ─── Global Error Handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled System Error on {request.url.path}: {type(exc).__name__}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal system error occurred. Stadium Operations team has been notified."}
    )

# ─── Startup DB Init ──────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()

# ─── API Routers ──────────────────────────────────────────────────────────────
app.include_router(auth_router,         prefix="/api/auth",           tags=["Auth"])
app.include_router(assistant_router,    prefix="/api/assistant",      tags=["Assistant"])
app.include_router(crowd_router,        prefix="/api/crowd",          tags=["Crowd"])
app.include_router(transport_router,    prefix="/api/transport",      tags=["Transport"])
app.include_router(sustainability_router, prefix="/api/sustainability", tags=["Sustainability"])
app.include_router(decision_router,     prefix="/api/decision",       tags=["Decision"])
app.include_router(ws_router,           prefix="/ws",                 tags=["WebSocket"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "FIFA WC 2026 Stadium Operations Core",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "redis": "connected" if _redis_client else "in-memory fallback"}
