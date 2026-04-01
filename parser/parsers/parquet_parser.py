"""
Parquet log parser -- reads Apache Parquet files using pyarrow.

Parquet is a common format for high-frequency sensor traces in
modern semiconductor fabs (e.g. Vendor C dry etch sensor logs).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def parse(content: bytes) -> list[dict]:
    """Parse Parquet file bytes into a list of dicts (one per row)."""
    if isinstance(content, str):
        content = content.encode("latin-1")

    try:
        import pyarrow as pa          # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        logger.warning(
            "pyarrow not installed — Parquet parsing unavailable. "
            "Install with: python -m pip install pyarrow"
        )
        return []

    try:
        buf = pa.BufferReader(content)
        table = pq.read_table(buf)
    except Exception as exc:
        logger.error("Parquet read failed: %s", exc)
        return []

    records: list[dict] = []
    for row in table.to_pylist():
        rec: dict = {}
        for k, v in row.items():
            if v is None:
                rec[k] = ""
            elif hasattr(v, "isoformat"):
                rec[k] = v.isoformat()
            else:
                rec[k] = v
        records.append(rec)

    return records
