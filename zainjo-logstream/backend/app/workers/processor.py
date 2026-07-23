"""
Log processing worker.

Consumes ParsedSyslog objects from the ingestion queue and:
1. Looks up the source by IP address
2. Applies filter rules (user blocking, regex matching)
3. Calls the vendor-specific parser
4. Writes the entry to PostgreSQL (batched)
5. Appends raw message to flat file
6. Enqueues accepted logs for SIEM forwarding
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.log import SyslogEntry
from app.models.source import LogSource
from app.models.filter import FilterRule, BlockedUser
from app.models.audit import AuditLog
from app.parsers import get_parser
from app.syslog.parser import ParsedSyslog

logger = logging.getLogger(__name__)

# Queue for SIEM forwarder
siem_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=50000)

# In-memory cache for sources and filter rules
# Refreshed every 60 seconds to avoid hammering the DB
_source_cache: dict[str, dict] = {}         # ip_address -> source dict
_filter_cache: dict[str, list[dict]] = {}   # source_id -> list of rule dicts
_cache_lock = asyncio.Lock()
_cache_last_refresh: float = 0
_USERNAME_RE = re.compile(
    r"(?i)\b(?:user|username|operator|principal)\s*[=:\s]+\s*['\"]?([A-Za-z0-9_.@-]+)"
)


def invalidate_processing_cache() -> None:
    """Force the next processor pass to reload sources and filter rules."""
    global _cache_last_refresh
    _cache_last_refresh = 0


def _host_variants(value: Optional[str]) -> set[str]:
    """Return stable hostname forms for matching FQDNs and short names."""
    if not value:
        return set()
    normalized = value.strip().lower().rstrip(".")
    if not normalized:
        return set()
    variants = {normalized}
    if "." in normalized and ":" not in normalized:
        variants.add(normalized.split(".", 1)[0])
    return variants


async def _refresh_cache(session: AsyncSession) -> None:
    global _source_cache, _filter_cache, _cache_last_refresh
    import time
    now = time.monotonic()
    if now - _cache_last_refresh < 60:
        return

    async with _cache_lock:
        # Double check after acquiring lock
        if now - _cache_last_refresh < 60:
            return

        # Load sources
        result = await session.execute(select(LogSource).where(LogSource.enabled == True))
        sources = result.scalars().all()
        new_src: dict[str, dict] = {}
        for s in sources:
            source_info = {
                "id": s.id,
                "name": s.name,
                "vendor": s.vendor.lower(),
                "system_type": s.system_type,
            }
            # Sources commonly identify themselves in the syslog hostname
            # field. Index both the configured network address and host/name
            # aliases so operators do not have to manually maintain a second
            # hostname mapping.
            aliases = _host_variants(s.ip_address) | _host_variants(s.name)
            for alias in aliases:
                new_src[alias] = source_info
        _source_cache = new_src

        # Load filter rules
        result = await session.execute(
            select(FilterRule).where(FilterRule.enabled == True)
        )
        rules = result.scalars().all()
        new_flt: dict[str, list[dict]] = {}
        for rule in rules:
            result2 = await session.execute(
                select(BlockedUser).where(BlockedUser.filter_rule_id == rule.id)
            )
            blocked = result2.scalars().all()
            entry = {
                "id": rule.id,
                "name": rule.name,
                "field": rule.field,
                "pattern_type": rule.pattern_type,
                "action": rule.action,
                "patterns": [bu.pattern for bu in blocked],
            }
            new_flt.setdefault(rule.source_id, []).append(entry)
        _filter_cache = new_flt

        _cache_last_refresh = now
        logger.debug("Source/filter cache refreshed: %d sources, %d rule-sets", len(_source_cache), len(_filter_cache))


def _matches_rule(field_value: Optional[str], rule: dict) -> Optional[str]:
    """Return the matched pattern string if field_value triggers the rule, else None."""
    if not field_value:
        return None
    for pattern in rule["patterns"]:
        match rule["pattern_type"]:
            case "exact":
                if field_value.lower() == pattern.lower():
                    return pattern
            case "contains":
                if pattern.lower() in field_value.lower():
                    return pattern
            case "regex":
                try:
                    if re.search(pattern, field_value, re.IGNORECASE):
                        return pattern
                except re.error:
                    pass
    return None


def _find_source(parsed: ParsedSyslog) -> Optional[dict]:
    """Resolve a source by transport IP first, then syslog hostname."""
    for candidate in (parsed.source_ip, parsed.hostname):
        for alias in _host_variants(candidate):
            source = _source_cache.get(alias)
            if source:
                return source
    return None


def _infer_vendor(parsed: ParsedSyslog) -> str:
    """Infer a vendor for an auto-discovered source from common identifiers."""
    haystack = " ".join(
        value for value in (parsed.hostname, parsed.app_name, parsed.message, parsed.raw)
        if value
    ).lower()
    signatures = (
        ("huawei", ("huawei", "nce", "u2020", "neteco", "prs", "tacacs")),
        ("nokia", ("nokia", "netact", "manta ray", "mantaray")),
        ("ericsson", ("ericsson", "enm", "cenm")),
    )
    for vendor, needles in signatures:
        if any(needle in haystack for needle in needles):
            return vendor
    return "unknown"


def _discovered_source(parsed: ParsedSyslog) -> dict:
    """Represent an unconfigured sender without creating an unbounded DB row."""
    return {
        "id": None,
        "name": parsed.hostname or parsed.source_ip,
        "vendor": _infer_vendor(parsed),
        "system_type": "Auto-discovered",
    }


def _extract_username_fallback(text: str) -> Optional[str]:
    match = _USERNAME_RE.search(text or "")
    return match.group(1).strip("\"'") if match else None


async def _write_to_file(source_info: Optional[dict], raw: str, received_at: datetime) -> None:
    """Append raw syslog line to vendor-specific daily flat file."""
    try:
        vendor = (source_info or {}).get("vendor", "unknown")
        date_str = received_at.strftime("%Y-%m-%d")
        base = Path(settings.storage_path) / "raw" / vendor
        base.mkdir(parents=True, exist_ok=True)
        fname = base / f"{date_str}.log"
        # Append in text mode — fast non-blocking write
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_append, fname, raw)
    except Exception:
        logger.exception("Failed to write log to file")


def _sync_append(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.write("\n")


# Batch accumulator
_BATCH_SIZE = 200
_BATCH_TIMEOUT = 2.0  # seconds


async def processor_worker(worker_id: int) -> None:
    """
    Main log processor coroutine. Run N of these concurrently.
    Each worker pulls from the shared log_queue.
    """
    from app.syslog.listener import log_queue

    batch: list[SyslogEntry] = []
    audit_batch: list[AuditLog] = []
    last_flush = asyncio.get_event_loop().time()

    logger.info("Processor worker #%d started", worker_id)

    async with AsyncSessionLocal() as session:
        while True:
            # Drain the queue with a timeout so we can flush periodically
            try:
                parsed: ParsedSyslog = await asyncio.wait_for(log_queue.get(), timeout=_BATCH_TIMEOUT)
            except asyncio.TimeoutError:
                parsed = None

            if parsed is not None:
                await _refresh_cache(session)
                configured_source = _find_source(parsed)
                source_info = configured_source or _discovered_source(parsed)

                # ── Determine drop status ──────────────────────────────────
                is_dropped = False
                drop_reason = None
                rule_id = None
                rule_name = None
                matched_pattern = None

                # Run vendor parser to get fields (even before filtering)
                vendor = source_info["vendor"]
                vendor_parser = get_parser(vendor) if vendor else None
                parsed_fields_obj = vendor_parser.parse(parsed.message or parsed.raw) if vendor_parser else None
                parsed_fields_dict = parsed_fields_obj.to_dict() if parsed_fields_obj else {}
                username = (
                    parsed_fields_obj.username if parsed_fields_obj else None
                ) or _extract_username_fallback(parsed.message or parsed.raw)
                if username and "username" not in parsed_fields_dict:
                    parsed_fields_dict["username"] = username

                if configured_source:
                    rules = _filter_cache.get(configured_source["id"], [])
                    for rule in rules:
                        field = rule["field"]
                        if field == "username":
                            field_val = username
                        elif field == "hostname":
                            field_val = parsed.hostname
                        else:
                            field_val = parsed.message

                        matched = _matches_rule(field_val, rule)
                        if matched:
                            is_dropped = True
                            drop_reason = f"Matched filter rule '{rule['name']}'"
                            rule_id = rule["id"]
                            rule_name = rule["name"]
                            matched_pattern = matched
                            break

                now = datetime.now(timezone.utc)

                entry = SyslogEntry(
                    received_at=now,
                    log_timestamp=parsed.log_timestamp,
                    source_ip=parsed.source_ip,
                    source_id=source_info["id"],
                    source_name=source_info["name"],
                    vendor=source_info["vendor"],
                    hostname=parsed.hostname,
                    app_name=parsed.app_name,
                    proc_id=parsed.proc_id,
                    msg_id=parsed.msg_id,
                    facility=parsed.facility,
                    severity=parsed.severity,
                    severity_name=parsed.severity_name,
                    raw_message=parsed.raw,
                    message=parsed.message,
                    parsed_fields=parsed_fields_dict if parsed_fields_dict else None,
                    username=username,
                    is_dropped=is_dropped,
                    drop_reason=drop_reason,
                    forwarded_to_siem=False,
                    processed=True,
                )
                batch.append(entry)

                # Audit entry for dropped logs
                if is_dropped:
                    audit_batch.append(AuditLog(
                        timestamp=now,
                        source_ip=parsed.source_ip,
                        source_name=source_info["name"],
                        vendor=source_info["vendor"],
                        username=username,
                        raw_message=parsed.raw,
                        action="drop",
                        reason=drop_reason or "filter matched",
                        rule_id=rule_id,
                        rule_name=rule_name,
                        matched_pattern=matched_pattern,
                    ))

                # Enqueue accepted logs for SIEM forwarding
                if not is_dropped and settings.siem_enabled:
                    try:
                        siem_queue.put_nowait({
                            "source": source_info["name"],
                            "vendor": source_info["vendor"],
                            "timestamp": now.isoformat(),
                            "username": username,
                            "severity": parsed.severity_name,
                            "raw_message": parsed.raw,
                            "parsed_fields": parsed_fields_dict,
                        })
                    except asyncio.QueueFull:
                        pass  # Don't block processor if SIEM queue is full

                # Write raw line to file (non-blocking)
                asyncio.create_task(_write_to_file(source_info, parsed.raw, now))

            # ── Flush batch to DB ──────────────────────────────────────────
            now_time = asyncio.get_event_loop().time()
            if len(batch) >= _BATCH_SIZE or (batch and (now_time - last_flush) >= _BATCH_TIMEOUT):
                try:
                    session.add_all(batch)
                    if audit_batch:
                        session.add_all(audit_batch)
                    await session.commit()
                    batch.clear()
                    audit_batch.clear()
                    last_flush = now_time
                except Exception:
                    logger.exception("DB batch insert failed")
                    await session.rollback()
                    batch.clear()
                    audit_batch.clear()
