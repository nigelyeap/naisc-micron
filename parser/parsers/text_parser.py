"""
Unstructured text event-log parser.

Uses regex patterns to extract timestamps, event codes, machine IDs,
and severity levels from free-form text lines.
"""

from __future__ import annotations

import re

# Timestamp patterns (ordered by specificity)
_TS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("iso",     re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)")),
    ("us_date", re.compile(r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})")),
    ("syslog",  re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")),
    ("time_only", re.compile(r"(\d{2}:\d{2}:\d{2}(?:\.\d+)?)")),
]

# Event / alarm codes  (e.g. EVT-001, ALM_1234, ERR0042)
_EVENT_CODE = re.compile(r"\b([A-Z]{2,5}[-_]?\d{2,6})\b")

# Machine / tool IDs  (e.g. TOOL-A01, EQ_102, Chamber-3)
_MACHINE_ID = re.compile(
    r"(?:Machine:|Tool:|Equipment:)\s*(\w+)"
    r"|\b((?:TOOL|EQ|CHAMBER|UNIT|MODULE|MACHINE|MCH|PM|TM)[-_]?\w{1,10})\b",
    re.I,
)

# Severity keywords
_SEVERITY_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:CRITICAL|FATAL|CRIT)\b", re.I), "CRITICAL"),
    (re.compile(r"\b(?:ERROR|ERR|FAULT|ALARM|ALM|FAIL)\b", re.I), "ERROR"),
    (re.compile(r"\b(?:WARNING|WARN|CAUTION)\b", re.I), "WARNING"),
    (re.compile(r"\b(?:INFO|INFORMATION|NOTICE)\b", re.I), "INFO"),
    (re.compile(r"\b(?:DEBUG|TRACE|VERBOSE)\b", re.I), "DEBUG"),
]


def parse(content: str | bytes) -> list[dict]:
    """Parse unstructured text event log."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    records: list[dict] = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        rec: dict = {"_raw": line}

        # Timestamp
        for ts_name, ts_re in _TS_PATTERNS:
            m = ts_re.search(line)
            if m:
                rec["timestamp"] = m.group(1)
                rec["_ts_format"] = ts_name
                break

        # Event code
        m = _EVENT_CODE.search(line)
        if m:
            rec["event_code"] = m.group(1)

        # Machine ID
        m = _MACHINE_ID.search(line)
        if m:
            rec["machine_id"] = m.group(1) or m.group(2)

        # Severity
        for sev_re, sev_label in _SEVERITY_MAP:
            if sev_re.search(line):
                rec["severity"] = sev_label
                break

        # Message -- everything after timestamp (if found)
        if "timestamp" in rec:
            ts_end = line.find(rec["timestamp"]) + len(rec["timestamp"])
            msg = line[ts_end:].strip().lstrip("-:] ")
            rec["message"] = msg
        else:
            rec["message"] = line

        records.append(rec)

    return records
