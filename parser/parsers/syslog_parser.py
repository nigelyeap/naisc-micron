"""
Syslog format parser.

Extracts priority, timestamp, hostname, process, PID, and message.
Also attempts key-value extraction from the message body.
"""

from __future__ import annotations

import re

# RFC 3164-style:  <PRI>TIMESTAMP HOSTNAME PROCESS[PID]: MESSAGE
_SYSLOG_RE = re.compile(
    r"<(?P<priority>\d{1,3})>"
    r"\s*(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    r"\s+(?P<hostname>\S+)"
    r"\s+(?P<process>[^\[:\s]+)"
    r"(?:\[(?P<pid>\d+)\])?"
    r":\s*(?P<message>.*)"
)

# Fallback: <PRI> followed by free text
_SYSLOG_SIMPLE = re.compile(
    r"<(?P<priority>\d{1,3})>\s*(?P<message>.*)"
)

_KV_IN_MSG = re.compile(r"([\w.-]+)=(\"[^\"]*\"|'[^']*'|\S+)")


def _parse_message_kv(message: str) -> dict[str, str]:
    """Extract key=value pairs from a syslog message body."""
    pairs: dict[str, str] = {}
    for m in _KV_IN_MSG.finditer(message):
        key = m.group(1)
        val = m.group(2).strip("\"'")
        pairs[key] = val
    return pairs


def parse(content: str | bytes) -> list[dict]:
    """Parse syslog-formatted content."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    records: list[dict] = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        rec: dict = {}

        m = _SYSLOG_RE.match(line)
        if m:
            rec["priority"] = m.group("priority")
            rec["timestamp"] = m.group("timestamp")
            rec["hostname"] = m.group("hostname")
            rec["process"] = m.group("process")
            rec["pid"] = m.group("pid") or ""
            rec["message"] = m.group("message")
        else:
            m2 = _SYSLOG_SIMPLE.match(line)
            if m2:
                rec["priority"] = m2.group("priority")
                rec["message"] = m2.group("message")
            else:
                rec["_raw"] = line
                rec["_parse_error"] = "no syslog pattern match"
                records.append(rec)
                continue

        # Extract KV pairs from message
        msg_kv = _parse_message_kv(rec.get("message", ""))
        if msg_kv:
            rec["message_fields"] = msg_kv
            rec.update({f"msg.{k}": v for k, v in msg_kv.items()})

        rec["_raw"] = line
        records.append(rec)

    return records
