"""
SIEM forwarding worker.

Reads from siem_queue and POSTs batches to the configured SIEM URL.
Failed batches are retried with exponential backoff and then written
to a dead-letter file to prevent log loss.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.config import settings
from app.workers.processor import siem_queue

logger = logging.getLogger(__name__)


async def forwarder_worker() -> None:
    """Long-running coroutine that forwards accepted logs to the SIEM."""
    logger.info("SIEM forwarder worker started — target: %s", settings.siem_url)

    async with httpx.AsyncClient(timeout=settings.siem_timeout) as client:
        while True:
            batch: list[dict] = []

            # Collect up to batch_size messages within 2 seconds
            deadline = asyncio.get_event_loop().time() + 2.0
            while len(batch) < settings.siem_batch_size:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(siem_queue.get(), timeout=remaining)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            if not batch:
                continue

            await _forward_with_retry(client, batch)


async def _forward_with_retry(client: httpx.AsyncClient, batch: list[dict]) -> None:
    """Try to POST the batch to SIEM with exponential backoff."""
    payload = {"logs": batch, "count": len(batch)}
    delay = settings.siem_retry_delay

    for attempt in range(1, settings.siem_retry_attempts + 1):
        try:
            response = await client.post(
                settings.siem_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code < 400:
                logger.debug("Forwarded %d logs to SIEM (attempt %d)", len(batch), attempt)
                return
            else:
                logger.warning(
                    "SIEM returned HTTP %d on attempt %d/%d",
                    response.status_code, attempt, settings.siem_retry_attempts,
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning(
                "SIEM forward attempt %d/%d failed: %s",
                attempt, settings.siem_retry_attempts, exc,
            )

        if attempt < settings.siem_retry_attempts:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)  # Exponential back-off, cap at 30s

    # All retries exhausted — write to dead-letter file
    await _write_dead_letter(batch)


async def _write_dead_letter(batch: list[dict]) -> None:
    """Persist failed batch to disk so no logs are lost."""
    try:
        dl_dir = Path(settings.storage_path) / "failed"
        dl_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        dl_file = dl_dir / f"siem_failed_{ts}.jsonl"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_write_dl, dl_file, batch)
        logger.error(
            "SIEM forwarding failed after %d attempts — %d logs saved to %s",
            settings.siem_retry_attempts, len(batch), dl_file,
        )
    except Exception:
        logger.exception("Failed to write dead-letter file — logs may be lost!")


def _sync_write_dl(path: Path, batch: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for item in batch:
            fh.write(json.dumps(item) + "\n")
