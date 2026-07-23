"""
Nokia vendor parser (NetAct / Manta Ray).
Extracts: username, command, object_name, result.
"""
import re
import logging
from app.parsers.base import BaseParser, ParsedFields

logger = logging.getLogger(__name__)

_PATTERNS: list[re.Pattern] = [
    # Nokia NetAct audit log: "user=xxx command=yyy object=zzz result=ok"
    re.compile(
        r"(?i)user[=:\s]+(?P<username>\S+)"
        r"(?:.*?(?:command|cmd)[=:\s]+(?P<command>[^,;\n]+))?"
        r"(?:.*?(?:object|obj|managed-object)[=:\s]+(?P<object_name>[^,;\n]+))?"
        r"(?:.*?(?:result|status)[=:\s]+(?P<result>[^,;\n]+))?",
        re.DOTALL,
    ),
    # Manta Ray: "MO:<object> User:<username> Operation:<command> Result:<result>"
    re.compile(
        r"(?i)(?:MO|Object)[:\s]+(?P<object_name>[^,;\n\s]+)"
        r".*?User[:\s]+(?P<username>[^,;\n\s]+)"
        r"(?:.*?(?:Operation|Command)[:\s]+(?P<command>[^,;\n]+))?"
        r"(?:.*?Result[:\s]+(?P<result>[^,;\n]+))?",
        re.DOTALL,
    ),
    # Generic Nokia audit
    re.compile(
        r"(?i)(?:login|session)\s+(?:for\s+)?(?:user\s+)?(?P<username>\w[\w@.\-]+)"
        r"(?:\s+(?P<command>(?:login|logout|session)[^\s,;]*))?"
        r"(?:.*?(?:success|fail|denied))?",
        re.DOTALL,
    ),
]

_RESULT_RE = re.compile(r"(?i)\b(?P<result>success|fail(?:ed)?|denied|error|ok|accepted|rejected)\b")


class NokiaParser(BaseParser):

    def parse(self, message: str) -> ParsedFields:
        pf = ParsedFields()
        for pattern in _PATTERNS:
            m = pattern.search(message)
            if m:
                groups = m.groupdict()
                pf.username = _clean(groups.get("username"))
                pf.command = _clean(groups.get("command"))
                pf.object_name = _clean(groups.get("object_name"))
                pf.result = _clean(groups.get("result"))
                break

        if not pf.result:
            rm = _RESULT_RE.search(message)
            if rm:
                pf.result = rm.group("result").lower()

        return pf


def _clean(val: str | None) -> str | None:
    if not val:
        return None
    return val.strip().strip("\"'").strip().rstrip(",;").strip() or None
