"""FastAPI Application - Main entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import RequestLoggingMiddleware
from src.api.routers import agents, mcp, oauth, workflow
from src.config.logging import get_logger, setup_logging
from src.mcp import shutdown_mcp_manager
from src.secrets import init_secrets_manager
from src.storage import close_database, init_database
from src.tools.builtin import register_builtin_tools

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging()
    await init_database()
    init_secrets_manager()
    register_builtin_tools()
    logger.info("application_started", name="Magure AI Platform", version="0.1.0")
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

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/v1")
app.include_router(mcp.router, prefix="/api/v1")
app.include_router(oauth.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")


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
