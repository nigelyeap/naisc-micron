"""
JSON log parser -- handles single objects, arrays, and NDJSON.
Recursively flattens nested semiconductor sensor data and expands
measurement arrays into individual rows.
"""

from __future__ import annotations

import json
from typing import Any


def _collect_scalars(obj: dict, prefix: str = "") -> dict[str, Any]:
    """Collect all scalar (non-dict, non-list-of-dict) fields with dot notation."""
    out: dict[str, Any] = {}
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_collect_scalars(v, key))
        elif isinstance(v, list):
            if not v or not isinstance(v[0], dict):
                out[key] = v  # list of scalars -- keep as-is
            # list of dicts -- skip (handled separately)
        else:
            out[key] = v
    return out


def _find_list_of_dicts(obj: dict, prefix: str = "") -> list[tuple[str, list[dict]]]:
    """Recursively find all list-of-dicts fields at any nesting depth."""
    found: list[tuple[str, list[dict]]] = []
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, list) and v and isinstance(v[0], dict):
            found.append((key, v))
        elif isinstance(v, dict):
            found.extend(_find_list_of_dicts(v, key))
    return found


def _extract_records(obj: dict, context: dict | None = None) -> list[dict]:
    """
    Recursively expand nested list-of-dicts into flat records.
    Each leaf measurement/event becomes its own record.
    """
    if context is None:
        context = {}

    # Collect scalar fields at all levels of this object
    scalars = _collect_scalars(obj)
    merged = {**context, **scalars}

    # Find expandable arrays (list of dicts) at any depth
    list_fields = _find_list_of_dicts(obj)

    if not list_fields:
        # Leaf -- emit one record with all accumulated scalars
        return [merged] if merged else []

    # Expand each list-of-dicts field
    # If there are multiple independent list fields (e.g. SensorData AND Events),
    # expand each separately with the shared context
    records: list[dict] = []
    for field_path, items in list_fields:
        for item in items:
            # Get scalars from this list item
            item_scalars = _collect_scalars(item, field_path)
            item_context = {**merged, **item_scalars}

            # Check if this item has its own nested list-of-dicts
            sub_lists = _find_list_of_dicts(item, field_path)
            if sub_lists:
                # Recurse deeper
                records.extend(_extract_records(item, merged))
            else:
                # Leaf -- emit record
                records.append(item_context)

    return records


def parse(content: str | bytes) -> list[dict]:
    """Parse JSON content into a list of flat dicts."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    content = content.strip()
    records: list[dict] = []

    # Try full JSON first
    try:
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.extend(_extract_records(item))
                else:
                    records.append({"value": item})
        elif isinstance(data, dict):
            records.extend(_extract_records(data))
        else:
            records.append({"value": data})
        return records
    except json.JSONDecodeError:
        pass

    # Try NDJSON (one JSON object per line)
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.extend(_extract_records(obj))
            else:
                records.append({"value": obj})
        except json.JSONDecodeError:
            records.append({"_raw": line, "_parse_error": "invalid JSON"})

    return records
