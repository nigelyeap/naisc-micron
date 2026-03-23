"""
Key-value pair log parser.

Handles `key=value` logs with quoted values and various delimiters.
"""

from __future__ import annotations

import re

# Matches key=value, key="quoted value", key='quoted value'
_KV_PATTERN = re.compile(
    r"""([\w.\-/]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+))"""
)


def _parse_kv_line(line: str) -> dict[str, str]:
    """Extract all key=value pairs from a single line."""
    pairs: dict[str, str] = {}
    for m in _KV_PATTERN.finditer(line):
        key = m.group(1)
        # Pick whichever capture group matched
        value = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4)
        )
        pairs[key] = value
    return pairs


def parse(content: str | bytes) -> list[dict]:
    """Parse key=value formatted log content."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    records: list[dict] = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        pairs = _parse_kv_line(line)
        if pairs:
            pairs["_raw"] = line
            records.append(pairs)
        else:
            # Line with no KV pairs -- keep as raw
            records.append({"_raw": line, "_parse_error": "no key=value pairs found"})

    return records
