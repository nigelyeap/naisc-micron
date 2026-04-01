"""
LLM fallback parser -- sends unparseable log samples to Claude
for structured field extraction.

Gracefully degrades when no API key is available.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from parser.normalizer import UnifiedLogRecord

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
You are a semiconductor equipment log parser.  Given the raw log content
below, extract as many structured fields as possible.

Return ONLY a JSON array of objects.  Each object should have these fields
where applicable:

- timestamp (ISO 8601 string)
- tool_id (equipment identifier)
- module_id (chamber / sub-system, or null)
- event_type (one of: SENSOR_READ, ALARM, EVENT, RECIPE, WAFER_OP, UNKNOWN)
- severity (one of: INFO, WARNING, ERROR, CRITICAL)
- parameters (object of key-value pairs -- sensor readings, set-points, etc.)
- message (human-readable summary of the record)

Do NOT include any markdown, explanation, or wrapping -- only raw JSON.

--- RAW LOG ---
{content}
--- END ---
"""


def parse_with_llm(
    content: str,
    api_key: str = "",
    model: str = "claude-sonnet-4-6",
    source_file: str = "",
    max_sample_chars: int = 4000,
) -> list[UnifiedLogRecord]:
    """
    Use Claude API to parse log content that rule-based parsers couldn't handle.

    Returns an empty list with a logged warning if no API key is provided.
    """

    if not api_key:
        logger.warning("No Anthropic API key provided -- LLM fallback skipped.")
        return []

    # Trim to a reasonable sample size
    sample = content[:max_sample_chars]

    try:
        import anthropic  # type: ignore
    except ImportError:
        logger.warning(
            "anthropic package not installed. "
            "Install with: python -m pip install anthropic"
        )
        return []

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": _EXTRACTION_PROMPT.format(content=sample),
                }
            ],
        )

        # Extract text from response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        # Parse the JSON response
        parsed = _parse_llm_response(text)

        # Convert to UnifiedLogRecords
        records: list[UnifiedLogRecord] = []
        for item in parsed:
            records.append(_item_to_record(item, source_file))

        return records

    except Exception as exc:
        logger.error("LLM fallback failed: %s", exc)
        return []


def _parse_llm_response(text: str) -> list[dict]:
    """Parse the JSON array from the LLM response."""
    text = text.strip()

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code fences
    import re
    m = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass

    # Try finding array brackets
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse LLM response as JSON")
    return []


def _item_to_record(item: dict, source_file: str) -> UnifiedLogRecord:
    """Convert an LLM-extracted dict to a UnifiedLogRecord."""
    warnings: list[str] = ["parsed by LLM fallback"]

    # Timestamp
    ts = None
    ts_str = item.get("timestamp", "")
    if ts_str:
        try:
            ts = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            warnings.append(f"LLM timestamp not parseable: {ts_str}")
    if ts is None:
        ts = datetime.now(timezone.utc)
        warnings.append("no valid timestamp from LLM, using current time")

    # Event type validation
    valid_events = {"SENSOR_READ", "ALARM", "EVENT", "RECIPE", "WAFER_OP", "UNKNOWN"}
    event_type = item.get("event_type", "UNKNOWN")
    if event_type not in valid_events:
        event_type = "UNKNOWN"

    # Severity validation
    valid_sevs = {"INFO", "WARNING", "ERROR", "CRITICAL"}
    severity = item.get("severity", "INFO")
    if severity not in valid_sevs:
        severity = "INFO"

    # Parameters
    params = item.get("parameters", {})
    if not isinstance(params, dict):
        params = {}

    # Add message to params if present
    msg = item.get("message", "")
    if msg:
        params["message"] = msg

    return UnifiedLogRecord(
        id=str(uuid.uuid4()),
        source_file=source_file,
        source_format="llm_parsed",
        timestamp=ts,
        tool_id=item.get("tool_id", "UNKNOWN"),
        module_id=item.get("module_id"),
        event_type=event_type,
        severity=severity,
        parameters=params,
        raw_content=str(item),
        confidence=0.45,
        parse_warnings=warnings,
    )
