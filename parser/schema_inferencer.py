"""
Auto schema inference -- discover fields in parsed records and map them
to a unified semiconductor-equipment log schema.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SchemaMapping:
    """Result of schema inference."""
    field_mappings: dict[str, str]         # source_field --> unified_field
    detected_fields: list[str]             # all source fields seen
    unmapped_fields: list[str]             # fields that couldn't be mapped
    confidence_scores: dict[str, float]    # per-mapping confidence


# ---------------------------------------------------------------------------
# Known field patterns --> unified names
# ---------------------------------------------------------------------------

_TIMESTAMP_NAMES = {
    "datetime", "date_time", "timestamp", "time", "created_at", "logged_at",
    "event_time", "log_time", "record_time", "ts", "dt", "date",
    "start_time", "end_time", "eventtime", "logtime",
}

_TOOL_ID_NAMES = {
    "tool_id", "toolid", "machine_id", "machineid", "equipment_id",
    "equipmentid", "tool", "machine", "eq_id", "device_id", "deviceid",
    "system_id", "systemid",
}

_MODULE_ID_NAMES = {
    "module_id", "moduleid", "chamber", "chamber_id", "chamberid",
    "module", "sub_system", "subsystem", "component", "unit",
}

_EVENT_NAMES = {
    "event", "event_type", "eventtype", "event_code", "eventcode",
    "alarm", "alarm_code", "alarmcode", "message_type", "messagetype",
    "type", "action",
}

_SEVERITY_NAMES = {
    "severity", "level", "priority", "log_level", "loglevel",
    "sev", "prio",
}

# Sensor / measurement patterns: regex --> unified name
_SENSOR_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"temp(?:erature)?(?:_?[cf])?$", re.I), "temperature_c"),
    (re.compile(r"press(?:ure)?(?:_?(?:pa|mbar|torr|mtorr))?$", re.I), "pressure_pa"),
    (re.compile(r"(?:gas_?)?flow(?:_?(?:sccm|slm))?$", re.I), "flow_sccm"),
    (re.compile(r"power(?:_?[wk]?w)?$", re.I), "power_w"),
    (re.compile(r"voltage(?:_?v)?$", re.I), "voltage_v"),
    (re.compile(r"current(?:_?[am]a?)?$", re.I), "current_a"),
    (re.compile(r"rf_?(?:power|fwd|refl)", re.I), "rf_power_w"),
    (re.compile(r"bias(?:_?v(?:oltage)?)?$", re.I), "bias_v"),
    (re.compile(r"humidity(?:_?(?:rh|pct))?$", re.I), "humidity_pct"),
    (re.compile(r"rpm|rotation", re.I), "rotation_rpm"),
    (re.compile(r"thickness", re.I), "thickness_nm"),
    (re.compile(r"position", re.I), "position_mm"),
]


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict/list using dot notation."""
    items: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                items.update(_flatten(v, new_key))
            else:
                items[new_key] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{prefix}.{i}"
            if isinstance(v, (dict, list)):
                items.update(_flatten(v, new_key))
            else:
                items[new_key] = v
    else:
        if prefix:
            items[prefix] = obj
    return items


def _normalise_key(key: str) -> str:
    """Lower-case, strip whitespace, replace spaces/hyphens with underscores."""
    return re.sub(r"[\s\-]+", "_", key.strip()).lower()


def _looks_like_timestamp(value: Any) -> bool:
    """Heuristic check if a value looks like a timestamp string."""
    if not isinstance(value, str):
        return False
    # ISO-ish or common date patterns
    ts_patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}/\d{2}/\d{4}",
        r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}",
    ]
    return any(re.search(p, value) for p in ts_patterns)


class SchemaInferencer:
    """Infer a unified schema mapping from a list of parsed records."""

    def infer(self, records: list[dict]) -> SchemaMapping:
        if not records:
            return SchemaMapping({}, [], [], {})

        # Flatten all records and collect unique field names
        flat_records = [_flatten(r) for r in records]
        all_fields: set[str] = set()
        for rec in flat_records:
            all_fields.update(rec.keys())

        detected_fields = sorted(all_fields)
        mappings: dict[str, str] = {}
        confidences: dict[str, float] = {}

        for src_field in detected_fields:
            norm = _normalise_key(src_field.split(".")[-1])  # use leaf name
            mapped, conf = self._map_field(norm, src_field, flat_records)
            if mapped:
                mappings[src_field] = mapped
                confidences[src_field] = conf

        unmapped = [f for f in detected_fields if f not in mappings]

        return SchemaMapping(
            field_mappings=mappings,
            detected_fields=detected_fields,
            unmapped_fields=unmapped,
            confidence_scores=confidences,
        )

    def _map_field(
        self, norm_key: str, src_field: str, records: list[dict]
    ) -> tuple[str | None, float]:
        """Try to map a normalised field name to a unified field."""

        # Timestamp
        if norm_key in _TIMESTAMP_NAMES:
            return "timestamp", 0.90
        # Check values heuristically
        sample_vals = [r.get(src_field) for r in records[:5] if src_field in r]
        if sample_vals and all(_looks_like_timestamp(v) for v in sample_vals if v is not None):
            return "timestamp", 0.70

        # Tool / equipment ID
        if norm_key in _TOOL_ID_NAMES:
            return "tool_id", 0.90

        # Module / chamber
        if norm_key in _MODULE_ID_NAMES:
            return "module_id", 0.90

        # Event type
        if norm_key in _EVENT_NAMES:
            return "event_type", 0.85

        # Severity
        if norm_key in _SEVERITY_NAMES:
            return "severity", 0.85

        # Sensor patterns
        for pattern, unified_name in _SENSOR_PATTERNS:
            if pattern.search(norm_key):
                return unified_name, 0.80

        return None, 0.0
