"""
Scheduled cleanup worker.

Runs periodically to:
- Compress raw log files older than `compress_after_days`
- Delete raw log files older than `retention_days`
- Optionally prune old DB records (configurable)
"""
import asyncio
import gzip
import logging
import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)


def _compress_file(path: Path) -> None:
    """Gzip a file in-place (replaces .log with .log.gz)."""
    gz_path = path.with_suffix(path.suffix + ".gz")
    with open(path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    path.unlink()
    logger.info("Compressed %s -> %s", path, gz_path)


def _parse_date_from_filename(name: str) -> datetime | None:
    """Extract date from filenames like '2024-01-15.log' or '2024-01-15.log.gz'."""
    stem = name.split(".")[0]
    try:
        return datetime.strptime(stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


async def run_cleanup() -> None:
    """Perform log file compression and deletion based on retention policy."""
    logger.info("Running log cleanup job")
    storage_root = Path(settings.storage_path) / "raw"
    now = datetime.now(timezone.utc)
    compress_threshold = now - timedelta(days=settings.compress_after_days)
    delete_threshold = now - timedelta(days=settings.retention_days)

    loop = asyncio.get_event_loop()

    if not storage_root.exists():
        logger.debug("Storage path %s does not exist — skipping cleanup", storage_root)
        return

    for vendor_dir in storage_root.iterdir():
        if not vendor_dir.is_dir():
            continue
        for log_file in vendor_dir.iterdir():
            name = log_file.name
            file_date = _parse_date_from_filename(name)
            if file_date is None:
                continue

            if file_date < delete_threshold:
                # Delete (compressed or not)
                try:
                    log_file.unlink()
                    logger.info("Deleted old log file: %s", log_file)
                except OSError as exc:
                    logger.error("Failed to delete %s: %s", log_file, exc)

            elif file_date < compress_threshold and not name.endswith(".gz"):
                # Compress
                try:
                    await loop.run_in_executor(None, _compress_file, log_file)
                except Exception:
                    logger.exception("Failed to compress %s", log_file)

    # Move old entries to archive directory
    await _archive_old_entries()
    logger.info("Log cleanup job complete")


async def _archive_old_entries() -> None:
    """Move compressed files to the archive directory."""
    try:
        raw_root = Path(settings.storage_path) / "raw"
        archive_root = Path(settings.storage_path) / "archive"
        now = datetime.now(timezone.utc)
        archive_threshold = now - timedelta(days=settings.compress_after_days * 2)

        if not raw_root.exists():
            return

        for vendor_dir in raw_root.iterdir():
            if not vendor_dir.is_dir():
                continue
            for gz_file in vendor_dir.glob("*.log.gz"):
                file_date = _parse_date_from_filename(gz_file.name)
                if file_date and file_date < archive_threshold:
                    dest_dir = archive_root / vendor_dir.name
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest = dest_dir / gz_file.name
                    shutil.move(str(gz_file), str(dest))
                    logger.info("Archived %s -> %s", gz_file, dest)
    except Exception:
        logger.exception("Archive step failed")


def start_cleanup_scheduler() -> AsyncIOScheduler:
    """Create and start the APScheduler cleanup job."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_cleanup,
        trigger="interval",
        hours=settings.cleanup_interval_hours,
        id="log_cleanup",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # Run immediately on startup
    )
    scheduler.start()
    logger.info(
        "Cleanup scheduler started — interval: %dh, retention: %d days, compress after: %d days",
        settings.cleanup_interval_hours,
        settings.retention_days,
        settings.compress_after_days,
    )
    return scheduler
