"""
Huawei vendor parser.
Extracts: username, operation, device, result, action.

Huawei syslog messages from NCE/U2020 systems follow patterns like:
  User [username] performed [operation] on [device]: [result]
  OperationLog: User=backupuser, Operation=Login, Device=10.x.x.x, Result=Success
"""
import re
import logging
from app.parsers.base import BaseParser, ParsedFields

logger = logging.getLogger(__name__)

_PATTERNS: list[re.Pattern] = [
    # OperationLog key=value style
    re.compile(
        r"(?i)(?:OperationLog|AuditLog|OperLog)"
        r".*?User[=:\s]+(?P<username>\S+)"
        r".*?(?:Operation|Oper)[=:\s]+(?P<operation>[^,;\n]+)"
        r"(?:.*?(?:Device|Host)[=:\s]+(?P<device>[^,;\n]+))?"
        r"(?:.*?Result[=:\s]+(?P<result>[^,;\n]+))?",
        re.DOTALL,
    ),
    # User [name] login/logout/operation
    re.compile(
        r"(?i)User\s+['\"]?(?P<username>\w[\w@.\-]+)['\"]?\s+"
        r"(?P<operation>(?:login|logout|config|delete|create|modify|query|backup|restore|reset)\w*)"
        r"(?:\s+on\s+(?P<device>\S+))?"
        r"(?:.*?(?:success|fail|error|denied))?",
        re.DOTALL,
    ),
    # TACACS / AAA style: user=xxx cmd=yyy
    re.compile(
        r"(?i)(?:user|username)=(?P<username>\S+)"
        r"(?:.*?(?:cmd|command|oper)=(?P<operation>[^\s,;]+))?"
        r"(?:.*?(?:device|host|nas-ip)=(?P<device>[^\s,;]+))?"
        r"(?:.*?(?:priv-lvl|result|auth)=(?P<result>[^\s,;]+))?",
        re.DOTALL,
    ),
    # Generic "user performed action"
    re.compile(
        r"(?i)(?:user|operator)\s*[:\-=]\s*(?P<username>\S+)"
        r".*?(?:action|operation)\s*[:\-=]\s*(?P<action>[^\s,;]+)",
        re.DOTALL,
    ),
]

_ACTION_RE = re.compile(
    r"(?i)\b(?P<action>login|logout|configure|delete|create|modify|backup|restore|query|upload|download|reset|enable|disable|approve|reject)\b"
)


class HuaweiParser(BaseParser):

    def parse(self, message: str) -> ParsedFields:
        pf = ParsedFields()
        for pattern in _PATTERNS:
            m = pattern.search(message)
            if m:
                groups = m.groupdict()
                pf.username = _clean(groups.get("username"))
                pf.operation = _clean(groups.get("operation"))
                pf.device = _clean(groups.get("device"))
                pf.result = _clean(groups.get("result"))
                pf.action = _clean(groups.get("action"))
                break

        # Fallback action extraction
        if not pf.action:
            am = _ACTION_RE.search(message)
            if am:
                pf.action = am.group("action").lower()

        return pf


def _clean(val: str | None) -> str | None:
    if not val:
        return None
    return val.strip().strip("\"'").strip().rstrip(",;").strip() or None
