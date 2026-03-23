"""
XML log parser -- uses ElementTree.
Handles namespaces (strips them for cleaner keys) and flattens nested elements.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


_NS_RE = re.compile(r"\{[^}]+\}")


def _strip_ns(tag: str) -> str:
    """Remove namespace URI from a tag name."""
    return _NS_RE.sub("", tag)


def _element_to_dict(elem: ET.Element, prefix: str = "") -> dict[str, Any]:
    """Recursively convert an XML element to a flat dict with dot notation."""
    result: dict[str, Any] = {}
    tag = _strip_ns(elem.tag)
    key_base = f"{prefix}.{tag}" if prefix else tag

    # Attributes
    for attr_name, attr_val in elem.attrib.items():
        attr_name = _strip_ns(attr_name)
        result[f"{key_base}.@{attr_name}"] = attr_val

    # Text content
    if elem.text and elem.text.strip():
        result[key_base] = elem.text.strip()

    # Children
    for child in elem:
        result.update(_element_to_dict(child, key_base))

    return result


def parse(content: str | bytes) -> list[dict]:
    """Parse XML content into a list of flat dicts."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    records: list[dict] = []

    try:
        # Strip XML declaration encoding issues
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return [{"_raw": content[:500], "_parse_error": f"XML parse error: {exc}"}]

    # Heuristic: if root has children that look like repeated records,
    # each child becomes a record; otherwise the whole doc is one record.
    child_tags = [_strip_ns(c.tag) for c in root]
    unique_tags = set(child_tags)

    if len(child_tags) > 1 and len(unique_tags) <= 3:
        # Repeated children --> one record per child
        for child in root:
            rec = _element_to_dict(child)
            # Also capture root-level attributes
            for attr_name, attr_val in root.attrib.items():
                rec[f"_root.@{_strip_ns(attr_name)}"] = attr_val
            records.append(rec)
    else:
        # Single document --> one record
        records.append(_element_to_dict(root))

    return records
