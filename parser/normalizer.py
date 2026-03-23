"""
Unified normalisation -- converts parsed records + schema mapping
into UnifiedLogRecord instances.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from parser.schema_inferencer import SchemaMapping


@dataclass
class UnifiedLogRecord:
    id: str                          # UUID
    source_file: str
    source_format: str
    timestamp: datetime
    tool_id: str
    module_id: str | None
    event_type: str                  # SENSOR_READ, ALARM, EVENT, RECIPE, WAFER_OP, UNKNOWN
    severity: str                    # INFO, WARNING, ERROR, CRITICAL
    parameters: dict                 # normalized key-value pairs
    raw_content: str                 # original line/record
    confidence: float                # 0.0 - 1.0
    parse_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

_TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%b %d %H:%M:%S",       # syslog-style (no year)
    "%Y%m%d%H%M%S",
]

# ISO with timezone offset, e.g. 2024-01-01T00:00:00+09:00
_ISO_TZ_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"([+-]\d{2}:?\d{2})"
)


def _parse_timestamp(value: Any) -> tuple[datetime | None, str | None]:
    """Try to parse a timestamp string. Returns (datetime, warning)."""
    if isinstance(value, datetime):
        return value, None
    if not isinstance(value, str):
        return None, f"timestamp value is not a string: {value!r}"

    value = value.strip()

    # Handle ISO with timezone offset
    m = _ISO_TZ_RE.match(value)
    if m:
        dt_part, tz_part = m.group(1), m.group(2)
        # Python 3.7+ handles fromisoformat with tz
        try:
            return datetime.fromisoformat(value), None
        except ValueError:
            pass

    for fmt in _TS_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            # If syslog format (no year), attach current year
            if "%Y" not in fmt and "%y" not in fmt:
                dt = dt.replace(year=datetime.now().year)
            return dt, None
        except ValueError:
            continue

    return None, f"could not parse timestamp: {value!r}"


# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

def _mtorr_to_pa(v: float) -> float:
    return v * 0.133322


def _torr_to_pa(v: float) -> float:
    return v * 133.322


def _mbar_to_pa(v: float) -> float:
    return v * 100.0


def _psi_to_pa(v: float) -> float:
    return v * 6894.76


def _f_to_c(v: float) -> float:
    return (v - 32.0) * 5.0 / 9.0


def _k_to_c(v: float) -> float:
    return v - 273.15


_UNIT_CONVERTERS: dict[str, tuple[str, callable]] = {
    "mtorr":  ("pressure_pa", _mtorr_to_pa),
    "torr":   ("pressure_pa", _torr_to_pa),
    "mbar":   ("pressure_pa", _mbar_to_pa),
    "psi":    ("pressure_pa", _psi_to_pa),
    "fahrenheit": ("temperature_c", _f_to_c),
    "kelvin": ("temperature_c", _k_to_c),
}


def _try_numeric(value: Any) -> float | None:
    """Try to convert value to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Strip units suffix
        cleaned = re.sub(r"[^\d.\-eE+]", "", value.strip())
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def _detect_unit_suffix(field_name: str) -> str | None:
    """Return a unit key if the field name ends with a known unit."""
    lower = field_name.lower()
    for unit_key in _UNIT_CONVERTERS:
        if lower.endswith(unit_key) or lower.endswith(f"_{unit_key}"):
            return unit_key
    return None


# ---------------------------------------------------------------------------
# Severity inference
# ---------------------------------------------------------------------------

_SEVERITY_KEYWORDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:CRITICAL|FATAL|CRIT)\b", re.I), "CRITICAL"),
    (re.compile(r"\b(?:ERROR|ERR|FAULT|ALARM|ALM|FAIL(?:URE)?)\b", re.I), "ERROR"),
    (re.compile(r"\b(?:WARNING|WARN|CAUTION)\b", re.I), "WARNING"),
    (re.compile(r"\b(?:INFO|INFORMATION|NOTICE)\b", re.I), "INFO"),
]


def _infer_severity(record: dict, existing: str | None) -> str:
    """Infer severity from record content if not already set."""
    if existing and existing.upper() in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        return existing.upper()

    # Search through raw content and values
    search_text = " ".join(str(v) for v in record.values())
    for pattern, level in _SEVERITY_KEYWORDS:
        if pattern.search(search_text):
            return level
    return "INFO"


# ---------------------------------------------------------------------------
# Event type classification
# ---------------------------------------------------------------------------

_EVENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:ALARM|ALM|FAULT)\b", re.I), "ALARM"),
    (re.compile(r"\b(?:SENSOR|READING|MEASURE|TEMP|PRESS|FLOW)\b", re.I), "SENSOR_READ"),
    (re.compile(r"\b(?:RECIPE|PROCESS|STEP)\b", re.I), "RECIPE"),
    (re.compile(r"\b(?:WAFER|LOT|CASSETTE|FOUP)\b", re.I), "WAFER_OP"),
    (re.compile(r"\b(?:EVENT|EVT|LOG|STATUS)\b", re.I), "EVENT"),
]


def _classify_event(record: dict, existing: str | None) -> str:
    if existing and existing.upper() in ("SENSOR_READ", "ALARM", "EVENT", "RECIPE", "WAFER_OP"):
        return existing.upper()
    search_text = " ".join(str(v) for v in record.values())
    for pattern, etype in _EVENT_PATTERNS:
        if pattern.search(search_text):
            return etype
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

class Normalizer:
    """Convert parsed records + schema mapping into UnifiedLogRecords."""

    def normalize(
        self,
        records: list[dict],
        mapping: SchemaMapping,
        source_file: str = "",
        source_format: str = "",
    ) -> list[UnifiedLogRecord]:
        unified: list[UnifiedLogRecord] = []
        fm = mapping.field_mappings

        for rec in records:
            warnings: list[str] = []
            confidence = 1.0

            # --- Timestamp ---
            ts = None
            for src, dst in fm.items():
                if dst == "timestamp" and src in rec:
                    ts, warn = _parse_timestamp(rec[src])
                    if warn:
                        warnings.append(warn)
                    break
            if ts is None:
                # Try common keys directly
                for k in ("timestamp", "time", "datetime", "DateTime"):
                    if k in rec:
                        ts, warn = _parse_timestamp(rec[k])
                        if warn:
                            warnings.append(warn)
                        break
            if ts is None:
                ts = datetime.now(timezone.utc)
                warnings.append("no timestamp found, using current time")
                confidence -= 0.2

            # --- Tool ID ---
            tool_id = ""
            for src, dst in fm.items():
                if dst == "tool_id" and src in rec:
                    tool_id = str(rec[src])
                    break
            if not tool_id:
                for k in ("tool_id", "machine_id", "ToolID", "MachineID"):
                    if k in rec:
                        tool_id = str(rec[k])
                        break
            if not tool_id:
                tool_id = "UNKNOWN"
                confidence -= 0.1

            # --- Module ID ---
            module_id = None
            for src, dst in fm.items():
                if dst == "module_id" and src in rec:
                    module_id = str(rec[src])
                    break

            # --- Severity ---
            sev_val = None
            for src, dst in fm.items():
                if dst == "severity" and src in rec:
                    sev_val = str(rec[src])
                    break
            severity = _infer_severity(rec, sev_val)

            # --- Event type ---
            evt_val = None
            for src, dst in fm.items():
                if dst == "event_type" and src in rec:
                    evt_val = str(rec[src])
                    break
            event_type = _classify_event(rec, evt_val)

            # --- Parameters (everything else) ---
            skip_fields = {"_raw", "_parse_error", "_source", "_ts_format", "message_fields"}
            mapped_src_fields = set(fm.keys())
            params: dict[str, Any] = {}

            for key, value in rec.items():
                if key in skip_fields:
                    continue
                # Apply field mapping
                unified_key = fm.get(key, key)
                if unified_key in ("timestamp", "tool_id", "module_id", "severity", "event_type"):
                    continue

                # Try numeric conversion + unit conversion
                num = _try_numeric(value)
                unit = _detect_unit_suffix(unified_key)
                if num is not None and unit:
                    target_name, converter = _UNIT_CONVERTERS[unit]
                    params[target_name] = round(converter(num), 6)
                elif num is not None:
                    params[unified_key] = num
                else:
                    params[unified_key] = value

            # --- Raw content ---
            raw = rec.get("_raw", str(rec))

            # --- Confidence ---
            if rec.get("_parse_error"):
                confidence -= 0.3
                warnings.append(rec["_parse_error"])
            confidence = max(confidence, 0.0)

            unified.append(UnifiedLogRecord(
                id=str(uuid.uuid4()),
                source_file=source_file,
                source_format=source_format,
                timestamp=ts,
                tool_id=tool_id,
                module_id=module_id,
                event_type=event_type,
                severity=severity,
                parameters=params,
                raw_content=raw,
                confidence=round(confidence, 2),
                parse_warnings=warnings,
            ))

        return unified
