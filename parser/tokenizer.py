"""
Tokenizer -- annotates each field in a parsed record with a semantic
TokenType before schema inference.

Input:  list[dict]  (raw parsed records from any format parser)
Output: list[list[Token]]  (one Token per field, per record)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    TIMESTAMP       = auto()
    TOOL_ID         = auto()
    MODULE_ID       = auto()
    EVENT_TYPE      = auto()
    SEVERITY        = auto()
    PARAMETER_KEY   = auto()   # a numeric / measurement field
    PARAMETER_VALUE = auto()   # non-classified value
    RAW_CONTENT     = auto()   # _raw internal field
    UNKNOWN         = auto()


@dataclass
class Token:
    field_name:       str
    raw_value:        Any
    token_type:       TokenType
    confidence:       float          # 0.0 – 1.0


# ---------------------------------------------------------------------------
# Field-name lookup sets (mirrors schema_inferencer, kept local)
# ---------------------------------------------------------------------------

_TS_NAMES = {
    "datetime", "date_time", "timestamp", "time", "created_at",
    "logged_at", "event_time", "log_time", "record_time", "ts", "dt",
    "date", "start_time", "end_time", "eventtime", "logtime",
}

_TOOL_NAMES = {
    "tool_id", "toolid", "machine_id", "machineid", "equipment_id",
    "equipmentid", "tool", "machine", "eq_id", "device_id", "deviceid",
    "system_id", "systemid",
}

_MODULE_NAMES = {
    "module_id", "moduleid", "chamber", "chamber_id", "chamberid",
    "module", "sub_system", "subsystem", "component", "unit",
}

_EVENT_NAMES = {
    "event", "event_type", "eventtype", "event_code", "eventcode",
    "alarm", "alarm_code", "alarmcode", "message_type", "messagetype",
    "type", "action",
}

_SEVERITY_NAMES = {
    "severity", "level", "priority", "log_level", "loglevel", "sev", "prio",
}

_SEVERITY_VALUES = {"critical", "error", "warning", "warn", "info",
                    "debug", "fault", "alarm", "crit", "err"}

_SENSOR_RE = re.compile(
    r"temp(?:erature)?|press(?:ure)?|flow|power|voltage|current|"
    r"rf_?power|bias|humidity|rpm|rotation|thickness|position",
    re.I,
)

# Timestamp value heuristic
_TS_VALUE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{2}/\d{2}/\d{4}"
    r"|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}",
)

_NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")


def _norm_key(key: str) -> str:
    """Lowercase leaf name (after last dot), underscored."""
    leaf = key.split(".")[-1]
    return re.sub(r"[\s\-]+", "_", leaf.strip()).lower()


def _classify_by_name(norm: str) -> tuple[TokenType, float] | None:
    if norm in _TS_NAMES:
        return TokenType.TIMESTAMP, 0.90
    if norm in _TOOL_NAMES:
        return TokenType.TOOL_ID, 0.90
    if norm in _MODULE_NAMES:
        return TokenType.MODULE_ID, 0.90
    if norm in _EVENT_NAMES:
        return TokenType.EVENT_TYPE, 0.85
    if norm in _SEVERITY_NAMES:
        return TokenType.SEVERITY, 0.85
    if _SENSOR_RE.search(norm):
        return TokenType.PARAMETER_KEY, 0.80
    return None


def _classify_by_value(value: Any) -> tuple[TokenType, float] | None:
    if isinstance(value, str):
        v = value.strip()
        if _TS_VALUE_RE.search(v):
            return TokenType.TIMESTAMP, 0.70
        if v.lower() in _SEVERITY_VALUES:
            return TokenType.SEVERITY, 0.75
        if _NUMERIC_RE.match(v):
            return TokenType.PARAMETER_VALUE, 0.60
    if isinstance(value, (int, float)):
        return TokenType.PARAMETER_VALUE, 0.65
    return None


class Tokenizer:
    """
    Converts a list of parsed records into parallel token sequences.

    Each record dict produces one Token per field. The token type is
    determined first by field-name lookup, then by value-pattern matching,
    with the higher-confidence result winning.
    """

    def tokenize(self, records: list[dict]) -> list[list[Token]]:
        """
        Args:
            records: Raw parsed records from any format parser.

        Returns:
            A list of token sequences, one sequence per record.
            Each sequence contains one Token per field in that record.
        """
        result: list[list[Token]] = []
        for rec in records:
            result.append(self._tokenize_record(rec))
        return result

    def _tokenize_record(self, record: dict) -> list[Token]:
        tokens: list[Token] = []
        for field_name, value in record.items():
            if field_name == "_raw":
                tokens.append(Token(field_name, value, TokenType.RAW_CONTENT, 1.0))
                continue

            norm = _norm_key(field_name)

            name_result  = _classify_by_name(norm)
            value_result = _classify_by_value(value)

            if name_result and value_result:
                token_type, conf = (
                    name_result if name_result[1] >= value_result[1]
                    else value_result
                )
            elif name_result:
                token_type, conf = name_result
            elif value_result:
                token_type, conf = value_result
            else:
                token_type, conf = TokenType.UNKNOWN, 0.0

            tokens.append(Token(field_name, value, token_type, conf))

        return tokens
