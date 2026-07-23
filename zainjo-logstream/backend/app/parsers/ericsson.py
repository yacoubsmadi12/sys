"""
Ericsson vendor parser (ENM / cENM).
Extracts: username (user), activity, node, action.
"""
import re
import logging
from app.parsers.base import BaseParser, ParsedFields

logger = logging.getLogger(__name__)

_PATTERNS: list[re.Pattern] = [
    # ENM AuditLog: "USER:xxx ACTIVITY:yyy NODE:zzz ACTION:aaa"
    re.compile(
        r"(?i)USER[=:\s]+(?P<username>\S+)"
        r"(?:.*?ACTIVITY[=:\s]+(?P<activity>[^,;\n]+))?"
        r"(?:.*?NODE[=:\s]+(?P<node>[^,;\n]+))?"
        r"(?:.*?ACTION[=:\s]+(?P<action>[^,;\n]+))?",
        re.DOTALL,
    ),
    # cENM Kubernetes log style
    re.compile(
        r"(?i)(?:user|principal)[=:\s]+(?P<username>\S+)"
        r"(?:.*?(?:action|verb)[=:\s]+(?P<action>[^\s,;]+))?"
        r"(?:.*?(?:resource|node|ne)[=:\s]+(?P<node>[^\s,;]+))?"
        r"(?:.*?(?:result|status)[=:\s]+(?P<activity>[^\s,;]+))?",
        re.DOTALL,
    ),
    # Ericsson SSHD / security event
    re.compile(
        r"(?i)(?:Accepted|Failed)\s+\w+\s+for\s+(?P<username>\S+)"
        r"(?:\s+from\s+(?P<node>\S+))?",
        re.DOTALL,
    ),
]

_ACTION_RE = re.compile(
    r"(?i)\b(?P<action>login|logout|create|delete|modify|read|execute|import|export|backup|restore|activate|deactivate)\b"
)


class EricssonParser(BaseParser):

    def parse(self, message: str) -> ParsedFields:
        pf = ParsedFields()
        for pattern in _PATTERNS:
            m = pattern.search(message)
            if m:
                groups = m.groupdict()
                pf.username = _clean(groups.get("username"))
                pf.activity = _clean(groups.get("activity"))
                pf.node = _clean(groups.get("node"))
                pf.action = _clean(groups.get("action"))
                break

        if not pf.action:
            am = _ACTION_RE.search(message)
            if am:
                pf.action = am.group("action").lower()

        return pf


def _clean(val: str | None) -> str | None:
    if not val:
        return None
    return val.strip().strip("\"'").strip() or None
