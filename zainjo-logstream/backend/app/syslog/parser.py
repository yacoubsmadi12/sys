"""
Syslog message parser supporting RFC 3164 and RFC 5424.
"""
import re
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

SEVERITY_NAMES = {
    0: "EMERGENCY",
    1: "ALERT",
    2: "CRITICAL",
    3: "ERROR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
    7: "DEBUG",
}

FACILITY_NAMES = {
    0: "kern", 1: "user", 2: "mail", 3: "daemon",
    4: "auth", 5: "syslog", 6: "lpr", 7: "news",
    8: "uucp", 9: "cron", 10: "authpriv", 11: "ftp",
    16: "local0", 17: "local1", 18: "local2", 19: "local3",
    20: "local4", 21: "local5", 22: "local6", 23: "local7",
}

# RFC 5424 pattern
_RFC5424 = re.compile(
    r"<(?P<pri>\d{1,3})>"
    r"(?P<version>\d+) "
    r"(?P<timestamp>\S+) "
    r"(?P<hostname>\S+) "
    r"(?P<app_name>\S+) "
    r"(?P<proc_id>\S+) "
    r"(?P<msg_id>\S+) "
    r"(?P<structured_data>\S+|\[.*?\]+) "
    r"(?P<message>.*)",
    re.DOTALL,
)

# RFC 3164 pattern (more lenient)
_RFC3164 = re.compile(
    r"<(?P<pri>\d{1,3})>"
    r"(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    r"\s+(?P<hostname>\S+)"
    r"\s+(?P<app_name>[^\[:]+?)(?:\[(?P<proc_id>\d+)\])?"
    r":\s*(?P<message>.*)",
    re.DOTALL,
)

# Bare priority without standard timestamp
_BARE_PRI = re.compile(r"<(?P<pri>\d{1,3})>(?P<rest>.*)", re.DOTALL)


@dataclass
class ParsedSyslog:
    raw: str
    source_ip: str
    priority: Optional[int] = None
    facility: Optional[int] = None
    severity: Optional[int] = None
    severity_name: Optional[str] = None
    log_timestamp: Optional[datetime] = None
    hostname: Optional[str] = None
    app_name: Optional[str] = None
    proc_id: Optional[str] = None
    msg_id: Optional[str] = None
    message: str = ""
    rfc: str = "unknown"


def _decode_priority(pri_str: str) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Returns (priority, facility, severity)."""
    try:
        pri = int(pri_str)
        facility = pri >> 3
        severity = pri & 0x07
        return pri, facility, severity
    except (ValueError, TypeError):
        return None, None, None


def _parse_rfc5424_ts(ts_str: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp from RFC 5424."""
    if ts_str == "-":
        return None
    try:
        # Handle 'Z' suffix
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _parse_rfc3164_ts(ts_str: str) -> Optional[datetime]:
    """Parse BSD syslog timestamp (no year, no timezone)."""
    try:
        now = datetime.now(timezone.utc)
        # "Jan  1 00:00:00" -> add current year
        dt = datetime.strptime(ts_str.strip(), "%b %d %H:%M:%S")
        return dt.replace(year=now.year, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def parse_syslog(raw: str, source_ip: str) -> ParsedSyslog:
    """
    Parse a raw syslog string into a ParsedSyslog dataclass.
    Tries RFC 5424 first, then RFC 3164, then bare priority.
    """
    result = ParsedSyslog(raw=raw, source_ip=source_ip)

    # Try RFC 5424
    m = _RFC5424.match(raw)
    if m:
        result.rfc = "5424"
        pri, fac, sev = _decode_priority(m.group("pri"))
        result.priority = pri
        result.facility = fac
        result.severity = sev
        result.severity_name = SEVERITY_NAMES.get(sev) if sev is not None else None
        result.log_timestamp = _parse_rfc5424_ts(m.group("timestamp"))
        result.hostname = _nil(m.group("hostname"))
        result.app_name = _nil(m.group("app_name"))
        result.proc_id = _nil(m.group("proc_id"))
        result.msg_id = _nil(m.group("msg_id"))
        result.message = m.group("message").strip()
        return result

    # Try RFC 3164
    m = _RFC3164.match(raw)
    if m:
        result.rfc = "3164"
        pri, fac, sev = _decode_priority(m.group("pri"))
        result.priority = pri
        result.facility = fac
        result.severity = sev
        result.severity_name = SEVERITY_NAMES.get(sev) if sev is not None else None
        result.log_timestamp = _parse_rfc3164_ts(m.group("timestamp"))
        result.hostname = m.group("hostname")
        result.app_name = m.group("app_name").strip() if m.group("app_name") else None
        result.proc_id = m.group("proc_id")
        result.message = m.group("message").strip()
        return result

    # Bare priority fallback
    m = _BARE_PRI.match(raw)
    if m:
        result.rfc = "bare"
        pri, fac, sev = _decode_priority(m.group("pri"))
        result.priority = pri
        result.facility = fac
        result.severity = sev
        result.severity_name = SEVERITY_NAMES.get(sev) if sev is not None else None
        result.message = m.group("rest").strip()
        return result

    # Unparseable — store as raw message only
    result.rfc = "raw"
    result.message = raw
    return result


def _nil(val: Optional[str]) -> Optional[str]:
    """Return None for RFC 5424 nil value '-'."""
    return None if val in ("-", None) else val
