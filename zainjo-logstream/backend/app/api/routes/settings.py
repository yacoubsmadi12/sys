"""
Settings endpoint — exposes runtime-editable config values.
Reads from the active config and writes back to config.yaml.
"""
import os
from pathlib import Path
from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["Settings"])

# ── helpers ───────────────────────────────────────────────────────────────

def _config_path() -> Path:
    candidates = [
        Path(os.environ.get("CONFIG_PATH", "/etc/zainjo-logstream/config.yaml")),
        Path(__file__).parent.parent.parent.parent / "config.yaml",
        Path.cwd() / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    # fallback — write next to the backend folder
    return Path(__file__).parent.parent.parent.parent / "config.yaml"


def _load_yaml() -> dict:
    p = _config_path()
    if p.exists():
        with open(p) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_yaml(data: dict) -> None:
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# ── schemas ───────────────────────────────────────────────────────────────

class RetentionPolicy(BaseModel):
    retention_days: int        = Field(..., ge=1,  le=3650, description="Days before log files are deleted")
    compress_after_days: int   = Field(..., ge=1,  le=365,  description="Days before log files are compressed")
    syslog_workers: int        = Field(..., ge=1,  le=64,   description="Number of parallel processor workers")
    syslog_queue_size: int     = Field(..., ge=1000, le=1_000_000, description="In-memory ingestion queue size")
    siem_enabled: bool         = Field(..., description="Forward accepted logs to SIEM")
    siem_batch_size: int       = Field(..., ge=1,  le=5000, description="Logs per HTTP POST to SIEM")
    siem_url: str              = Field(..., description="SIEM endpoint URL")
    storage_path: str          = Field(..., description="Root directory for flat-file log storage")


class RetentionPolicyUpdate(BaseModel):
    retention_days: int        | None = Field(None, ge=1,  le=3650)
    compress_after_days: int   | None = Field(None, ge=1,  le=365)
    syslog_workers: int        | None = Field(None, ge=1,  le=64)
    syslog_queue_size: int     | None = Field(None, ge=1000, le=1_000_000)
    siem_enabled: bool         | None = None
    siem_batch_size: int       | None = Field(None, ge=1, le=5000)
    siem_url: str              | None = None
    storage_path: str          | None = None


# ── routes ────────────────────────────────────────────────────────────────

@router.get("", response_model=RetentionPolicy)
async def get_settings(
    _: Annotated[User, Depends(get_current_user)],
) -> RetentionPolicy:
    """Return current runtime settings (merged from config file + defaults)."""
    return RetentionPolicy(
        retention_days      = app_settings.retention_days,
        compress_after_days = app_settings.compress_after_days,
        syslog_workers      = app_settings.syslog_workers,
        syslog_queue_size   = app_settings.syslog_queue_size,
        siem_enabled        = app_settings.siem_enabled,
        siem_batch_size     = app_settings.siem_batch_size,
        siem_url            = app_settings.siem_url,
        storage_path        = app_settings.storage_path,
    )


@router.patch("", response_model=RetentionPolicy)
async def update_settings(
    body: RetentionPolicyUpdate,
    _: Annotated[User, Depends(require_admin)],
) -> RetentionPolicy:
    """Persist changed settings to config.yaml (admin only).
    Changes take effect on the next service restart."""
    cfg = _load_yaml()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")

    cfg.update(updates)
    _save_yaml(cfg)

    # Return the merged view (in-memory settings + just-written values)
    return RetentionPolicy(
        retention_days      = updates.get("retention_days",      app_settings.retention_days),
        compress_after_days = updates.get("compress_after_days", app_settings.compress_after_days),
        syslog_workers      = updates.get("syslog_workers",      app_settings.syslog_workers),
        syslog_queue_size   = updates.get("syslog_queue_size",   app_settings.syslog_queue_size),
        siem_enabled        = updates.get("siem_enabled",        app_settings.siem_enabled),
        siem_batch_size     = updates.get("siem_batch_size",     app_settings.siem_batch_size),
        siem_url            = updates.get("siem_url",            app_settings.siem_url),
        storage_path        = updates.get("storage_path",        app_settings.storage_path),
    )
