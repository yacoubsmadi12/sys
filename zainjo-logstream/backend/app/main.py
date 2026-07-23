"""
ZainJo LogStream — FastAPI application entry point.

Starts the syslog listeners and log processor workers on startup,
and tears them down cleanly on shutdown.
"""
import asyncio
import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import init_db

# ── Logging ───────────────────────────────────────────────────────────────────

Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.log_file,
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "root": {
        "level": settings.log_level,
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting ZainJo LogStream v%s", settings.app_version)

    # Ensure storage directories exist
    for sub in ["raw/huawei", "raw/nokia", "raw/ericsson", "raw/unknown",
                "archive", "processed", "failed"]:
        Path(settings.storage_path, sub).mkdir(parents=True, exist_ok=True)

    # Initialize DB tables
    await init_db()

    # Ensure default admin user exists
    await _ensure_default_admin()

    # Start syslog listeners
    from app.syslog.listener import start_listeners, log_queue
    listener_handles = await start_listeners()

    # Start processor workers
    from app.workers.processor import processor_worker
    processor_tasks = [
        asyncio.create_task(processor_worker(i), name=f"processor-{i}")
        for i in range(settings.syslog_workers)
    ]

    # Start SIEM forwarder
    from app.workers.forwarder import forwarder_worker
    forwarder_task = asyncio.create_task(forwarder_worker(), name="siem-forwarder")

    # Start cleanup scheduler
    from app.workers.cleanup import start_cleanup_scheduler
    scheduler = start_cleanup_scheduler()

    logger.info(
        "All workers started — API on :%d, Syslog on :%d",
        settings.api_port, settings.syslog_port,
    )

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down ZainJo LogStream...")
    scheduler.shutdown(wait=False)

    for h in listener_handles:
        if hasattr(h, "close"):
            h.close()

    for task in processor_tasks + [forwarder_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    logger.info("Shutdown complete")


async def _ensure_default_admin():
    """Create default admin user on first run if no users exist."""
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.auth.security import get_password_hash
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        if count == 0:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("Admin@LogStream1"),
                full_name="System Administrator",
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.warning(
                "Default admin user created — username: admin, password: Admin@LogStream1 "
                "— CHANGE THIS IMMEDIATELY!"
            )


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Centralized Syslog Collector for Telecom NOC environments",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from app.api.routes.auth import router as auth_router
    from app.api.routes.dashboard import router as dashboard_router
    from app.api.routes.logs import router as logs_router
    from app.api.routes.sources import router as sources_router
    from app.api.routes.filters import router as filters_router
    from app.api.routes.audit import router as audit_router
    from app.api.routes.settings import router as settings_router

    prefix = "/api"
    app.include_router(auth_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(logs_router, prefix=prefix)
    app.include_router(sources_router, prefix=prefix)
    app.include_router(filters_router, prefix=prefix)
    app.include_router(audit_router, prefix=prefix)
    app.include_router(settings_router, prefix=prefix)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,  # Use our own logging config
        workers=1,        # Must be 1 — background tasks don't survive fork
        loop="uvloop",
    )
