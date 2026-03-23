"""
Main pipeline orchestrator -- ties format detection, parsing, schema
inference, normalisation, and LLM fallback together.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

from parser.format_detector import FormatDetector, FormatDetection
from parser.llm_fallback import parse_with_llm
from parser.normalizer import Normalizer, UnifiedLogRecord
from parser.parsers import PARSER_MAP
from parser.schema_inferencer import SchemaInferencer, SchemaMapping

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    records: list[UnifiedLogRecord]
    format_detected: str
    schema_mapping: SchemaMapping
    parse_time_ms: float
    total_records: int
    failed_records: int
    avg_confidence: float


class LogParserPipeline:
    """Main entry point for parsing semiconductor equipment logs."""

    def __init__(self, anthropic_api_key: str = ""):
        self._detector = FormatDetector()
        self._inferencer = SchemaInferencer()
        self._normalizer = Normalizer()
        self._api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_file(self, file_path: str) -> ParseResult:
        """
        Parse a log file end-to-end:
        1. Read file (handle encoding detection)
        2. Detect format
        3. Route to appropriate parser
        4. Infer schema mapping
        5. Normalise to unified records
        6. Fall back to LLM if confidence is low
        7. Return ParseResult
        """
        start = time.perf_counter()

        # Read raw bytes
        try:
            with open(file_path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            logger.error("Cannot read file %s: %s", file_path, exc)
            return self._empty_result(time.perf_counter() - start)

        result = self._run_pipeline(raw, file_path)
        return result

    def parse_content(
        self, content: str | bytes, filename: str = ""
    ) -> ParseResult:
        """Parse log content directly (not from a file)."""
        return self._run_pipeline(content, filename)

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _run_pipeline(
        self, content: str | bytes, source: str
    ) -> ParseResult:
        start = time.perf_counter()

        # 1. Detect format
        try:
            detection = self._detector.detect(content)
        except Exception as exc:
            logger.error("Format detection failed: %s", exc)
            detection = FormatDetection("text", 0.1, "utf-8", "")

        fmt = detection.format_type

        # Make sure we have a text version for text-based parsers
        if isinstance(content, bytes):
            try:
                text = content.decode(detection.encoding)
            except (UnicodeDecodeError, LookupError):
                text = content.decode("latin-1")
        else:
            text = content

        # 2. Parse with the appropriate format parser
        parsed_records: list[dict] = []
        parse_succeeded = False

        parse_fn = PARSER_MAP.get(fmt)
        if parse_fn:
            try:
                if fmt == "binary":
                    parsed_records = parse_fn(
                        content if isinstance(content, bytes) else content.encode("latin-1")
                    )
                else:
                    parsed_records = parse_fn(text)
                parse_succeeded = True
            except Exception as exc:
                logger.error("Parser %s failed: %s", fmt, exc)

        # 3. Infer schema
        try:
            mapping = self._inferencer.infer(parsed_records)
        except Exception as exc:
            logger.error("Schema inference failed: %s", exc)
            mapping = SchemaMapping({}, [], [], {})

        # 4. Normalise
        try:
            unified = self._normalizer.normalize(
                parsed_records, mapping,
                source_file=source,
                source_format=fmt,
            )
        except Exception as exc:
            logger.error("Normalisation failed: %s", exc)
            unified = []

        # 5. Calculate average confidence
        avg_conf = (
            sum(r.confidence for r in unified) / len(unified)
            if unified else 0.0
        )

        # 6. LLM fallback if parsing failed or confidence is low
        if (not parse_succeeded or avg_conf < 0.5) and self._api_key:
            try:
                llm_records = parse_with_llm(
                    text, api_key=self._api_key, source_file=source
                )
                if llm_records:
                    # If rule-based gave nothing, use LLM results entirely;
                    # otherwise append LLM records for low-confidence entries
                    if not unified:
                        unified = llm_records
                    else:
                        unified.extend(llm_records)
                    fmt = f"{fmt}+llm"
            except Exception as exc:
                logger.error("LLM fallback error: %s", exc)

        # Recalculate stats after possible LLM additions
        avg_conf = (
            sum(r.confidence for r in unified) / len(unified)
            if unified else 0.0
        )
        failed = sum(1 for r in unified if r.confidence < 0.5)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return ParseResult(
            records=unified,
            format_detected=fmt,
            schema_mapping=mapping,
            parse_time_ms=round(elapsed_ms, 2),
            total_records=len(unified),
            failed_records=failed,
            avg_confidence=round(avg_conf, 3),
        )

    def _empty_result(self, elapsed: float) -> ParseResult:
        return ParseResult(
            records=[],
            format_detected="unknown",
            schema_mapping=SchemaMapping({}, [], [], {}),
            parse_time_ms=round(elapsed * 1000, 2),
            total_records=0,
            failed_records=0,
            avg_confidence=0.0,
        )
