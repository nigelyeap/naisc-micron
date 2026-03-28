"""
FastAPI application for the AI-Powered Smart Tool Log Parser backend.

Endpoints cover file upload/parsing, record querying, anomaly inspection,
analytics, and natural-language queries.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Make sibling packages (parser/, analytics/) importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.database import Database
from backend.nl_query import NLQueryEngine

# Attempt to import parser and analytics -- they may not be fully built yet
try:
    from parser.format_detector import FormatDetector
except ImportError:
    FormatDetector = None

try:
    from parser.pipeline import LogParserPipeline
except ImportError:
    LogParserPipeline = None

try:
    from analytics.anomaly_detector import AnomalyDetector
except ImportError:
    AnomalyDetector = None

try:
    from analytics.trend_analyzer import TrendAnalyzer
except ImportError:
    TrendAnalyzer = None

try:
    from analytics.cross_tool_comparator import CrossToolComparator
except ImportError:
    CrossToolComparator = None

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Smart Tool Log Parser API",
    description="Backend for the AI-Powered Semiconductor Equipment Log Parser",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
db = Database()
nl_engine = NLQueryEngine(db)
format_detector = FormatDetector() if FormatDetector else None

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class NLQueryRequest(BaseModel):
    question: str


class NLQueryResponse(BaseModel):
    generated_sql: str
    results: list[dict[str, Any]]
    explanation: str
    confidence: float


class UploadResponse(BaseModel):
    file_id: int
    filename: str
    format_detected: str | None
    total_records: int
    avg_confidence: float
    parse_time_ms: float
    anomalies_found: int


class HealthResponse(BaseModel):
    status: str
    database: str
    parser_available: bool
    analytics_available: bool
    nl_query_mode: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Health check -- reports component availability."""
    return HealthResponse(
        status="ok",
        database=db.db_path,
        parser_available=LogParserPipeline is not None,
        analytics_available=AnomalyDetector is not None,
        nl_query_mode="llm" if nl_engine._client else "fallback",
    )


# -- File upload & listing ---------------------------------------------------


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a log file, parse it, detect anomalies, and store results."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    start = time.perf_counter()

    # 1. Detect format
    detected_format: str | None = None
    if format_detector:
        detection = format_detector.detect(content)
        detected_format = detection.format_type

    # 2. Parse
    records: list[dict] = []
    avg_confidence = 0.0

    if LogParserPipeline is not None:
        # Write to a temp file so the pipeline can read it
        suffix = os.path.splitext(file.filename or "log.txt")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            pipeline = LogParserPipeline()
            result = pipeline.parse_file(tmp_path)
            # Normalise pipeline output to list[dict]
            if hasattr(result, "records"):
                for rec in result.records:
                    d = {}
                    if hasattr(rec, "__dict__"):
                        d = dict(rec.__dict__)
                    elif isinstance(rec, dict):
                        d = dict(rec)
                    # Ensure timestamp is a string
                    if "timestamp" in d and d["timestamp"] is not None:
                        ts = d["timestamp"]
                        if hasattr(ts, "isoformat"):
                            d["timestamp"] = ts.isoformat()
                        else:
                            d["timestamp"] = str(ts)
                    # Ensure parameters is a dict (not None)
                    if "parameters" not in d or d["parameters"] is None:
                        d["parameters"] = {}
                    records.append(d)
            avg_confidence = getattr(result, "avg_confidence", 0.0)
            if not avg_confidence and records:
                confs = [r.get("confidence", 0) for r in records]
                avg_confidence = sum(confs) / len(confs) if confs else 0.0
            if detected_format is None:
                detected_format = getattr(result, "format_detected", None)
        finally:
            os.unlink(tmp_path)
    else:
        # Minimal fallback: store raw lines as records so the file isn't lost
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
        for i, line in enumerate(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            records.append(
                {
                    "source_format": detected_format or "unknown",
                    "timestamp": None,
                    "tool_id": None,
                    "module_id": None,
                    "event_type": None,
                    "severity": None,
                    "parameters": {},
                    "raw_content": line,
                    "confidence": 0.0,
                    "parse_warnings": ["parser not available -- raw ingest only"],
                }
            )
        avg_confidence = 0.0

    elapsed_ms = (time.perf_counter() - start) * 1000

    # 3. Store in DB
    file_id = db.insert_file(
        filename=file.filename or "unknown",
        format_detected=detected_format,
        total_records=len(records),
        avg_confidence=avg_confidence,
        parse_time_ms=elapsed_ms,
    )
    inserted_ids = db.insert_records(file_id, records)

    # Build a mapping from the index-based record_id ("rec-0", "rec-1", ...)
    # generated by the anomaly detector back to the actual database row IDs.
    idx_to_db_id: dict[str, int] = {}
    for idx, db_id in enumerate(inserted_ids):
        idx_to_db_id[f"rec-{idx}"] = db_id

    # 4. Anomaly detection
    anomalies_found = 0
    if AnomalyDetector is not None and records:
        try:
            detector = AnomalyDetector()
            # Flatten parameters into top-level keys for the detector
            flat_records = []
            for r in records:
                flat = dict(r)
                params = flat.pop("parameters", {}) or {}
                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                    except (json.JSONDecodeError, TypeError):
                        params = {}
                flat.update(params)
                flat_records.append(flat)
            anomalies = detector.detect(flat_records)
            if anomalies:
                anomaly_dicts = []
                for a in anomalies:
                    ad = a.__dict__ if hasattr(a, "__dict__") else dict(a)
                    # Convert datetime to string and tuple to list for JSON
                    if "timestamp" in ad and hasattr(ad["timestamp"], "isoformat"):
                        ad["timestamp"] = ad["timestamp"].isoformat()
                    if "expected_range" in ad and isinstance(ad["expected_range"], tuple):
                        ad["expected_min"] = ad["expected_range"][0]
                        ad["expected_max"] = ad["expected_range"][1]
                        del ad["expected_range"]
                    # Map string record_id to actual database row ID
                    raw_rid = str(ad.get("record_id", ""))
                    if raw_rid in idx_to_db_id:
                        ad["record_id"] = str(idx_to_db_id[raw_rid])
                    anomaly_dicts.append(ad)
                db.insert_anomalies(anomaly_dicts)
                anomalies_found = len(anomaly_dicts)
        except Exception:
            logger.exception("Anomaly detection failed for file %s", file.filename)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "unknown",
        format_detected=detected_format,
        total_records=len(records),
        avg_confidence=round(avg_confidence, 4),
        parse_time_ms=round(elapsed_ms, 2),
        anomalies_found=anomalies_found,
    )


@app.get("/api/files")
def list_files():
    """List all uploaded files with metadata."""
    return db.get_files()


# -- Sample logs -------------------------------------------------------------

_SAMPLE_LOGS_DIR = Path(_PROJECT_ROOT) / "sample_logs"


@app.get("/api/samples")
def list_samples():
    """List available sample log filenames (non-.py files in sample_logs/)."""
    if not _SAMPLE_LOGS_DIR.is_dir():
        return []
    return [
        f.name
        for f in sorted(_SAMPLE_LOGS_DIR.iterdir())
        if f.suffix != ".py" and f.is_file()
    ]


@app.post("/api/samples/upload/{filename}", response_model=UploadResponse)
async def upload_sample(filename: str):
    """Parse and store a sample log file by name."""
    import io
    from starlette.datastructures import UploadFile as StarletteUploadFile

    path = _SAMPLE_LOGS_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found.")

    content = path.read_bytes()
    fake_file = StarletteUploadFile(filename=filename, file=io.BytesIO(content))
    return await upload_file(fake_file)


# -- Records -----------------------------------------------------------------


@app.get("/api/records")
def get_records(
    tool_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    file_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Query parsed log records with optional filters."""
    filters: dict[str, Any] = {}
    if tool_id:
        filters["tool_id"] = tool_id
    if event_type:
        filters["event_type"] = event_type
    if severity:
        filters["severity"] = severity
    if file_id is not None:
        filters["file_id"] = file_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date

    return db.query_records(filters=filters, limit=limit, offset=offset)


@app.get("/api/records/{record_id}")
def get_record(record_id: int):
    """Get a specific record by id."""
    record = db.get_record_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return record


# -- Anomalies ---------------------------------------------------------------


@app.get("/api/anomalies")
def get_anomalies(
    anomaly_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    parameter: Optional[str] = Query(None),
    record_id: Optional[int] = Query(None),
):
    """Get detected anomalies with optional filters."""
    filters: dict[str, Any] = {}
    if anomaly_type:
        filters["anomaly_type"] = anomaly_type
    if severity:
        filters["severity"] = severity
    if parameter:
        filters["parameter"] = parameter
    if record_id is not None:
        filters["record_id"] = record_id
    return db.query_anomalies(filters=filters)


# -- Analytics ---------------------------------------------------------------


@app.get("/api/analytics/summary")
def analytics_summary():
    """Overall summary statistics."""
    return db.get_summary_stats()


@app.get("/api/analytics/timeseries")
def analytics_timeseries(
    parameter: str = Query(..., description="Parameter name to chart"),
    tool_id: Optional[str] = Query(None),
):
    """Get timeseries data for a specific parameter."""
    data = db.get_parameter_timeseries(parameter, tool_id=tool_id)
    return {"parameter": parameter, "tool_id": tool_id, "data": data}


@app.get("/api/analytics/trends")
def analytics_trends(
    parameter: str = Query(..., description="Parameter name to analyse"),
    tool_id: Optional[str] = Query(None),
):
    """Get trend analysis for a parameter."""
    if TrendAnalyzer is None:
        # Fallback: return basic timeseries with simple stats
        data = db.get_parameter_timeseries(parameter, tool_id=tool_id)
        values = [d["value"] for d in data if isinstance(d.get("value"), (int, float))]
        if not values:
            return {"parameter": parameter, "trend": "insufficient data", "data": data}
        return {
            "parameter": parameter,
            "tool_id": tool_id,
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "stable",
            "data": data,
        }

    try:
        analyzer = TrendAnalyzer()
        records = db.query_records(
            filters={"tool_id": tool_id} if tool_id else None, limit=10000
        )
        result = analyzer.analyze(records, parameter)
        return result.__dict__ if hasattr(result, "__dict__") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/analytics/cross-tool")
def analytics_cross_tool(
    parameter: Optional[str] = Query(None),
):
    """Cross-tool comparison for a parameter (or general)."""
    if CrossToolComparator is None:
        # Fallback: group records by tool_id
        stats = db.get_summary_stats()
        return {
            "parameter": parameter,
            "tool_breakdown": stats.get("tool_breakdown", {}),
        }

    try:
        comparator = CrossToolComparator()
        records = db.query_records(limit=10000)
        result = comparator.compare(records, parameter)
        return result.__dict__ if hasattr(result, "__dict__") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -- Natural language query ---------------------------------------------------


@app.post("/api/query", response_model=NLQueryResponse)
def nl_query(req: NLQueryRequest):
    """Natural language query -- converts question to SQL and runs it."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = nl_engine.query(req.question)
    return NLQueryResponse(
        generated_sql=result.generated_sql,
        results=result.results,
        explanation=result.explanation,
        confidence=result.confidence,
    )
