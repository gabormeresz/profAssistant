"""
FastAPI application entry point.

Configures logging, sets up the lifespan (DB + MCP), adds CORS
middleware, and mounts all route modules.  Business logic lives in
``routes/`` and ``services/``.
"""

import logging
from config import LoggingConfig, DebugConfig, APIConfig

# Configure logging before anything else
logging.basicConfig(
    level=LoggingConfig.LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rate_limit import limiter

from services.database import db
from services.mcp_client import mcp_manager
from routes.auth import router as auth_router
from routes.generation import router as generation_router
from routes.conversations import router as conversations_router

logger = logging.getLogger(__name__)

# Log dummy graph status at import time
if DebugConfig.USE_DUMMY_GRAPH:
    logger.warning(
        "⚠️  DUMMY GRAPH ENABLED — course outline requests use fake data (no LLM calls)"
    )

# --------------------------------------------------------------------------- #
#  Application lifespan
# --------------------------------------------------------------------------- #


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler for FastAPI application startup/shutdown.

    Initializes MCP clients and database connections on startup,
    and cleans up on shutdown.
    """
    # Startup
    logger.info("Connecting to database...")
    await db.connect()
    logger.info("Initializing MCP clients...")
    await mcp_manager.initialize()
    logger.info("Application ready")

    yield

    # Shutdown
    logger.info("Cleaning up MCP clients...")
    await mcp_manager.cleanup()
    logger.info("Closing database connection...")
    await db.close()
    logger.info("Application stopped")


# --------------------------------------------------------------------------- #
#  App factory
# --------------------------------------------------------------------------- #

# In production (WARNING+), hide Swagger / ReDoc / OpenAPI schema entirely.
_is_production = LoggingConfig.LEVEL >= logging.WARNING

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# Wire rate-limiter into the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route modules ──
app.include_router(auth_router)
app.include_router(generation_router)
app.include_router(conversations_router)


# ── Health endpoint (always available, used by Docker HEALTHCHECK) ──
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
