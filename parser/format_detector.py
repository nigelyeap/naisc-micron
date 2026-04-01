"""
Content-based log format detection.

Inspects file content (not extension) to determine the log format.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass


@dataclass
class FormatDetection:
    """Result of format detection."""
    format_type: str        # json, xml, csv, syslog, kv, text, binary, parquet
    confidence: float       # 0.0 - 1.0
    encoding: str           # detected or assumed encoding
    sample_preview: str     # first ~200 chars of content for quick inspection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYSLOG_PRI = re.compile(r"^<\d{1,3}>")
_KV_PATTERN = re.compile(r"[\w.-]+=(?:\"[^\"]*\"|'[^']*'|\S+)")
_XML_TAG = re.compile(r"<[a-zA-Z/?!]")


def _non_printable_ratio(data: bytes, sample_size: int = 1024) -> float:
    """Return the fraction of non-printable, non-whitespace bytes."""
    sample = data[:sample_size]
    if not sample:
        return 0.0
    non_print = sum(
        1 for b in sample
        if b < 0x20 and b not in (0x09, 0x0A, 0x0D)  # tab, LF, CR
    )
    return non_print / len(sample)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class FormatDetector:
    """Detect log format from raw content."""

    # Ordered list of detection methods -- first high-confidence match wins.
    # Parquet must come before binary (Parquet files are binary).
    # KV must come before CSV because csv.Sniffer is overly eager.
    _DETECTORS: list[str] = [
        "_check_parquet",
        "_check_binary",
        "_check_json",
        "_check_xml",
        "_check_syslog",
        "_check_text_event_log",
        "_check_kv",
        "_check_csv",
        "_check_text",
    ]

    def detect(self, content: str | bytes, encoding: str = "utf-8") -> FormatDetection:
        """Detect the format of *content* and return a FormatDetection."""
        raw_bytes: bytes
        text: str

        if isinstance(content, bytes):
            raw_bytes = content
            # Try the given encoding; fall back to latin-1 (never fails)
            try:
                text = content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                try:
                    text = content.decode("utf-8-sig")
                    encoding = "utf-8-sig"
                except UnicodeDecodeError:
                    text = content.decode("latin-1")
                    encoding = "latin-1"
        else:
            text = content
            raw_bytes = content.encode(encoding, errors="replace")

        preview = text[:200]

        for method_name in self._DETECTORS:
            method = getattr(self, method_name)
            result: FormatDetection | None = method(text, raw_bytes, encoding, preview)
            if result is not None:
                return result

        # Ultimate fallback
        return FormatDetection(
            format_type="text",
            confidence=0.2,
            encoding=encoding,
            sample_preview=preview,
        )

    # ------------------------------------------------------------------
    # Individual detectors (return None when they don't match)
    # ------------------------------------------------------------------

    def _check_parquet(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        """Detect Apache Parquet files by their 4-byte magic number PAR1."""
        if raw[:4] == b"PAR1":
            return FormatDetection("parquet", 0.99, enc, preview)
        return None

    def _check_binary(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        ratio = _non_printable_ratio(raw)
        if ratio > 0.10:
            return FormatDetection("binary", min(ratio + 0.4, 1.0), enc, preview)
        return None

    def _check_json(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        stripped = text.strip()
        if not stripped:
            return None
        # Quick check for JSON-ish start characters
        if stripped[0] not in ("{", "["):
            # Could still be NDJSON (one JSON object per line)
            first_line = stripped.split("\n", 1)[0].strip()
            if not first_line or first_line[0] not in ("{", "["):
                return None

        try:
            json.loads(stripped)
            return FormatDetection("json", 0.95, enc, preview)
        except json.JSONDecodeError:
            pass

        # Try NDJSON -- parse first few lines
        lines = stripped.split("\n")[:5]
        ok = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                ok += 1
            except json.JSONDecodeError:
                pass
        if ok >= 2:
            return FormatDetection("json", 0.85, enc, preview)
        return None

    def _check_xml(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        stripped = text.strip()
        if stripped.startswith("<?xml"):
            return FormatDetection("xml", 0.95, enc, preview)
        # Look for tags in first few lines
        head = stripped[:500]
        tags = _XML_TAG.findall(head)
        if len(tags) >= 2:
            return FormatDetection("xml", 0.80, enc, preview)
        return None

    def _check_syslog(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        lines = text.strip().split("\n")[:10]
        matches = sum(1 for l in lines if _SYSLOG_PRI.match(l.strip()))
        if matches >= 2 or (len(lines) == 1 and matches == 1):
            confidence = min(matches / max(len(lines), 1) + 0.3, 1.0)
            return FormatDetection("syslog", confidence, enc, preview)
        return None

    def _check_csv(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        try:
            sample = text[:4096]
            dialect = csv.Sniffer().sniff(sample)
            has_header = csv.Sniffer().has_header(sample)
            # Extra confidence if there's a header
            confidence = 0.80 if has_header else 0.65
            return FormatDetection("csv", confidence, enc, preview)
        except csv.Error:
            return None

    def _check_kv(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        lines = text.strip().split("\n")[:10]
        kv_lines = 0
        for line in lines:
            pairs = _KV_PATTERN.findall(line)
            if len(pairs) >= 2:
                kv_lines += 1
        if kv_lines >= 2 or (len(lines) == 1 and kv_lines == 1):
            confidence = min(kv_lines / max(len(lines), 1) + 0.3, 1.0)
            return FormatDetection("kv", confidence, enc, preview)
        return None

    def _check_text_event_log(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        """Detect structured text event logs (timestamps + multi-line event blocks)."""
        lines = text.strip().split("\n")[:20]
        # Look for lines starting with date patterns like MM/DD/YYYY or YYYY-MM-DD
        date_pattern = re.compile(
            r"^\d{1,2}/\d{1,2}/\d{4}\s+\d{2}:\d{2}:\d{2}"
            r"|^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
        )
        # Also look for event keywords
        event_keywords = re.compile(
            r"SYSTEM EVENT|SYSTEM WARNING|ALARM|FAULT|DEACTIVATE|ERROR|WARNING|EVENT",
            re.IGNORECASE,
        )
        date_lines = sum(1 for l in lines if date_pattern.match(l.strip()))
        keyword_lines = sum(1 for l in lines if event_keywords.search(l))
        if date_lines >= 2 and keyword_lines >= 1:
            return FormatDetection("text", 0.85, enc, preview)
        if date_lines >= 3:
            return FormatDetection("text", 0.75, enc, preview)
        return None

    def _check_text(
        self, text: str, raw: bytes, enc: str, preview: str
    ) -> FormatDetection | None:
        # Fallback -- everything that's printable text
        if text.strip():
            return FormatDetection("text", 0.50, enc, preview)
        return None
