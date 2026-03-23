"""
Binary / hex log parser.

Extracts readable ASCII strings, detects repeating byte patterns,
and attempts to read numeric values from common byte widths.
"""

from __future__ import annotations

import re
import struct
from typing import Any


# Minimum length for an ASCII string to be considered meaningful
_MIN_STRING_LEN = 4

# ASCII printable range
_ASCII_RE = re.compile(rb"[\x20-\x7E]{%d,}" % _MIN_STRING_LEN)


def _extract_strings(data: bytes) -> list[str]:
    """Extract readable ASCII strings from binary data."""
    return [m.group().decode("ascii") for m in _ASCII_RE.finditer(data)]


def _detect_repeating_patterns(data: bytes, max_period: int = 64) -> list[dict]:
    """Look for repeating byte patterns (fixed-length records)."""
    patterns: list[dict] = []
    for period in range(4, min(max_period + 1, len(data) // 3)):
        chunk = data[:period]
        repeats = 0
        for offset in range(period, len(data) - period + 1, period):
            if data[offset:offset + period] == chunk:
                repeats += 1
            else:
                break
        if repeats >= 2:
            patterns.append({
                "period_bytes": period,
                "repeats": repeats,
                "sample_hex": chunk.hex(),
            })
    return patterns


def _extract_numerics(data: bytes) -> list[dict]:
    """Try reading numeric values at 2-byte and 4-byte boundaries."""
    values: list[dict] = []
    # Read first 256 bytes worth of values to keep output manageable
    sample = data[:256]

    # 4-byte floats (little-endian)
    for offset in range(0, len(sample) - 3, 4):
        try:
            val = struct.unpack_from("<f", sample, offset)[0]
            # Filter out nonsense: NaN, inf, or astronomically large values
            if val != 0.0 and abs(val) < 1e12 and val == val:  # val==val filters NaN
                values.append({
                    "offset": offset,
                    "type": "float32_le",
                    "value": round(val, 6),
                })
        except struct.error:
            pass

    # 2-byte unsigned ints (little-endian) -- if not too many floats already
    if len(values) < 20:
        for offset in range(0, len(sample) - 1, 2):
            try:
                val = struct.unpack_from("<H", sample, offset)[0]
                if 1 <= val <= 65000:
                    values.append({
                        "offset": offset,
                        "type": "uint16_le",
                        "value": val,
                    })
            except struct.error:
                pass

    return values[:50]  # cap output


def parse(content: str | bytes) -> list[dict]:
    """Parse binary content, returning extracted information."""
    if isinstance(content, str):
        content = content.encode("latin-1")

    record: dict[str, Any] = {
        "total_bytes": len(content),
        "ascii_strings": _extract_strings(content),
        "repeating_patterns": _detect_repeating_patterns(content),
        "numeric_values": _extract_numerics(content),
        "hex_preview": content[:64].hex(" "),
    }

    # If we found meaningful ASCII strings, create a record per string too
    records: list[dict] = [record]
    for s in record["ascii_strings"]:
        records.append({"extracted_string": s, "_source": "binary_ascii"})

    return records
