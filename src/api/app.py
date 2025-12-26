"""FastAPI Application - Main entry point."""
from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports read env vars

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)
from src.api.middleware import RequestLoggingMiddleware
from src.api.routers import admin, agents, auth, knowledge, mcp, monitoring, oauth, secrets, workflow, workflows
from src.monitoring import MetricsMiddleware, get_metrics_router
from src.config.logging import get_logger, setup_logging
from src.config.settings import get_settings
from src.mcp import reconnect_mcp_servers, shutdown_mcp_manager
from src.secrets import init_secrets_manager
from src.storage import close_database, init_database
from src.tools.builtin import register_builtin_tools

logger = get_logger(__name__)
settings = get_settings()

# Rate limiter setup
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default] if settings.rate_limit_enabled else [],
    enabled=settings.rate_limit_enabled,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging()
    await init_database()
    init_secrets_manager()
    register_builtin_tools()
    # Reconnect MCP servers from database
    mcp_count = await reconnect_mcp_servers()
    logger.info("application_started", name="Magure AI Platform", version="0.1.0", mcp_servers=mcp_count)
    yield
    # Shutdown
    await shutdown_mcp_manager()
    await close_database()
    logger.info("application_stopped")


app = FastAPI(
    title="Magure AI Platform",
    description="Dynamic Agent Workflow Platform with Temporal",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Prometheus metrics middleware (captures HTTP request metrics)
if settings.monitoring_enabled:
    app.add_middleware(MetricsMiddleware)

# CORS middleware - using settings instead of hardcoded values
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(mcp.router, prefix="/api/v1")
app.include_router(oauth.router, prefix="/api/v1")
app.include_router(secrets.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")

# Prometheus metrics endpoint
if settings.monitoring_enabled:
    app.include_router(get_metrics_router())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Magure AI Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
