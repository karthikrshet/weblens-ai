import os
import sys

# Ensure repository root and app are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [root_dir, api_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.models.db import init_db
from app.api.v1.endpoints import router as api_v1_router
from app.security.ssrf import SSRFValidationError, InvalidURLError

# Initialize Database Schema
init_db()

app = FastAPI(
    title="WebLens AI API",
    description="Agentic Website Intelligence & Exploration Platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline';"
    return response


# Domain Exception Handlers (Safe responses without leaking internal network topologies)
@app.exception_handler(SSRFValidationError)
async def ssrf_exception_handler(request: Request, exc: SSRFValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Target destination is not allowed by security policy."},
    )


@app.exception_handler(InvalidURLError)
async def invalid_url_handler(request: Request, exc: InvalidURLError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# Register API Routers
app.include_router(api_v1_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "title": "WebLens AI",
        "tagline": "Agentic Website Intelligence & Exploration System",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
