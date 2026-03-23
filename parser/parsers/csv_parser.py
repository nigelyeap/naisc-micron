"""
CSV log parser -- auto-detects delimiter and header row.
"""

from __future__ import annotations

import csv
import io


def parse(content: str | bytes) -> list[dict]:
    """Parse CSV content into a list of dicts (one per row)."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    records: list[dict] = []

    try:
        sample = content[:4096]
        dialect = csv.Sniffer().sniff(sample)
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        # Fallback: assume comma-delimited with header
        dialect = csv.excel
        has_header = True

    reader = csv.reader(io.StringIO(content), dialect)
    rows = list(reader)

    if not rows:
        return records

    if has_header:
        headers = [h.strip() for h in rows[0]]
        data_rows = rows[1:]
    else:
        # Generate column names
        max_cols = max(len(r) for r in rows) if rows else 0
        headers = [f"col_{i}" for i in range(max_cols)]
        data_rows = rows

    for row in data_rows:
        if not any(cell.strip() for cell in row):
            continue  # skip blank lines
        rec: dict = {}
        for i, value in enumerate(row):
            key = headers[i] if i < len(headers) else f"col_{i}"
            rec[key] = value.strip()
        records.append(rec)

    return records
