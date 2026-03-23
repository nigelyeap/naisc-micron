# Smart Tool Log Parser (SLP)

**Micron @ AISG National AI Student Challenge**

AI-powered semiconductor equipment log parser that ingests diverse log formats, normalizes them into a unified schema, detects anomalies, and provides interactive analytics through a dark-themed dashboard.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample logs (if not already present)
python sample_logs/gen_all.py

# Run everything (backend + frontend)
python run.py
```

- **Backend API**: http://localhost:8000
- **Dashboard**: http://localhost:8501

You can also start them separately:

```bash
python run.py --backend   # API only
python run.py --frontend  # Dashboard only
```

---

## What It Does

1. **Ingests** semiconductor equipment logs in 7 formats (JSON, XML, CSV, syslog, key-value, plain text, binary)
2. **Detects format** automatically by inspecting file content, not extensions
3. **Parses** each format with a specialized parser, handling deeply nested structures (e.g. recursive JSON flattening for vendor sensor traces)
4. **Infers schema** to map vendor-specific fields to a unified `UnifiedLogRecord` (timestamp, tool_id, module_id, event_type, severity, parameters, confidence)
5. **Detects anomalies** using Z-score, IQR, rate-of-change, and missing-data methods
6. **Analyzes trends** with linear regression, moving averages, and drift detection
7. **Correlates faults** by linking alarm events to preceding sensor anomalies
8. **Compares tools** across a fleet to identify outlier equipment
9. **Generates summaries** in plain-English markdown
10. **Answers questions** in natural language (converts English to SQL via Claude API, with keyword fallback)

---

## Project Structure

```
NAISC Micron/
+-- run.py                    # Central launcher (backend + frontend)
+-- app.py                    # Streamlit dashboard (CSS, hero, sidebar, routing)
+-- test_app.py               # 123 tests across 14 sections
+-- requirements.txt
+-- .streamlit/config.toml    # Dark theme config
|
+-- pages/                    # Streamlit page modules
|   +-- upload.py             # Upload & Parse
|   +-- explorer.py           # Log Explorer
|   +-- analytics_page.py     # Analytics Dashboard
|   +-- nl_query.py           # Natural Language Query
|   +-- summary.py            # Summary Report
|
+-- parser/                   # Core parsing engine
|   +-- format_detector.py    # Content-based format detection
|   +-- pipeline.py           # Orchestrator: detect -> parse -> normalize
|   +-- schema_inferencer.py  # Auto-maps vendor fields to unified schema
|   +-- normalizer.py         # Produces UnifiedLogRecord dicts
|   +-- llm_fallback.py       # Claude API fallback for unknown formats
|   +-- parsers/
|       +-- json_parser.py    # Recursive nested JSON flattening
|       +-- xml_parser.py
|       +-- csv_parser.py
|       +-- syslog_parser.py
|       +-- kv_parser.py
|       +-- text_parser.py    # Regex-based unstructured text
|       +-- binary_parser.py  # Hex dump + pattern extraction
|
+-- analytics/                # Analysis engines
|   +-- anomaly_detector.py   # Z-score, IQR, rate-of-change, missing data
|   +-- trend_analyzer.py     # Linear regression, moving averages, drift
|   +-- fault_correlator.py   # Alarm-to-anomaly time-window correlation
|   +-- cross_tool_comparator.py  # Fleet-wide outlier detection
|   +-- summary_generator.py  # Markdown report generation
|
+-- backend/                  # FastAPI + SQLite
|   +-- app.py                # 11 API endpoints
|   +-- database.py           # Thread-safe SQLite (3 tables)
|   +-- nl_query.py           # English -> SQL conversion
|   +-- run.py                # Standalone backend launcher
|
+-- frontend/                 # API client
|   +-- api_client.py         # HTTP wrapper for all backend calls
|
+-- sample_logs/              # Synthetic demo data (8 files)
|   +-- gen_all.py            # Generator script
|   +-- vendor_a_sensor_trace.json
|   +-- vendor_b_sensor_trace.json
|   +-- euv_dose_recipe.xml
|   +-- sensor_readings.csv
|   +-- syslog_equipment.log
|   +-- kv_process_log.log
|   +-- event_log.txt
|   +-- binary_diagnostic.bin
|
+-- data/
    +-- logs.db               # SQLite database (auto-created)
```

---

## Architecture

```
  Log Files (7 formats)
        |
        v
  +-- Format Detector --+
  |   (content-based)   |
  +---------------------+
        |
        v
  +-- Parser Engine ----+      +-- Schema Inferencer --+
  |  json/xml/csv/...   | ---> |  auto-maps fields to  |
  +---------------------+      |  unified schema       |
        |                      +-----------------------+
        v
  +-- Normalizer -------+
  |  UnifiedLogRecord   |
  +---------------------+
        |
        +------+------+------+------+
        |      |      |      |      |
        v      v      v      v      v
     Anomaly  Trend  Fault  Cross  Summary
     Detect   Anal.  Corr.  Tool   Gen.
        |      |      |      |      |
        +------+------+------+------+
        |
        v
  +-- SQLite Database ---+
  |  log_files           |
  |  log_records         |
  |  anomalies           |
  +---------------------+
        |
        v
  +-- FastAPI Backend ---+      +-- Streamlit Frontend --+
  |  REST API (11 eps)   | <--> |  5-page dashboard      |
  +---------------------+      +------------------------+
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload and parse a log file |
| `GET` | `/api/files` | List all uploaded files |
| `GET` | `/api/records` | Query records (filters: tool_id, event_type, severity, file_id) |
| `GET` | `/api/records/{id}` | Get single record |
| `GET` | `/api/anomalies` | Query detected anomalies |
| `GET` | `/api/analytics/summary` | Overall statistics |
| `GET` | `/api/analytics/timeseries` | Parameter timeseries data |
| `GET` | `/api/analytics/trends` | Trend analysis for a parameter |
| `GET` | `/api/analytics/cross-tool` | Cross-tool comparison |
| `POST` | `/api/query` | Natural language query (English -> SQL) |

---

## Supported Log Formats

| Format | Example | Parser Approach |
|--------|---------|-----------------|
| **JSON** | Vendor sensor traces with deeply nested structures | Recursive flattening of nested arrays |
| **XML** | EUV dose recipes | Element/attribute extraction |
| **CSV** | Timestamped sensor readings | Standard CSV with header inference |
| **Syslog** | RFC 3164/5424 equipment logs | Priority + message parsing |
| **Key-Value** | Process parameter logs (`key=value` pairs) | Regex KV extraction |
| **Text** | Free-form event logs with timestamps | Pattern matching for dates, IDs, events |
| **Binary** | Diagnostic memory dumps | Hex dump + embedded string extraction |

Format detection is **content-based** -- file extensions are ignored. The detector inspects byte patterns, structure markers, and statistical properties to classify each file.

---

## Analytics Engines

| Engine | Method | What It Detects |
|--------|--------|-----------------|
| **Anomaly Detector** | Z-score, IQR, rate-of-change, missing data | Sensor readings outside normal range |
| **Trend Analyzer** | Linear regression, moving averages | Increasing/decreasing/stable trends, drift |
| **Fault Correlator** | Time-window analysis, co-occurrence matrix | Links between alarms and preceding anomalies |
| **Cross-Tool Comparator** | Fleet baseline, Z-score outlier detection | Equipment running outside fleet norms |
| **Summary Generator** | Template-based markdown | Human-readable analysis reports |

---

## Database Schema

**3 tables in SQLite (WAL mode, thread-safe):**

**`log_files`** -- Uploaded file metadata
- id, filename, format_detected, upload_time, total_records, avg_confidence, parse_time_ms

**`log_records`** -- Parsed and normalized records
- id, file_id (FK), source_format, timestamp, tool_id, module_id, event_type, severity, parameters_json, raw_content, confidence, parse_warnings_json

**`anomalies`** -- Detected anomalies
- id, record_id (TEXT), parameter, value, expected_min, expected_max, anomaly_type, severity, z_score, description, detected_at

---

## Testing

```bash
python test_app.py
```

**123 tests across 14 sections:**

1. Format Detection (10 tests)
2. Individual Parsers (15 tests)
3. Schema Inference (4 tests)
4. Full Pipeline -- end-to-end (32 tests)
5. Anomaly Detection (7 tests)
6. Trend Analyzer (5 tests)
7. Cross-Tool Comparator (3 tests)
8. Fault Correlator (1 test)
9. Summary Generator (3 tests)
10. Database Operations (13 tests)
11. Natural Language Query (4 tests)
12. FastAPI Endpoints (13 tests, requires backend)
13. Frontend API Client (2 tests)
14. Edge Cases (8 tests)

---

## Design System

The dashboard uses the **Obsidian Protocol** design system, inspired by semiconductor cleanroom monitoring interfaces:

- **0px corners** -- sharp, machined precision throughout
- **No-line rule** -- surface layer shifts instead of borders
- **Glow over shadow** -- ambient pink glow for active states
- **Scan-line texture** -- subtle horizontal pattern on backgrounds
- **Colors** -- Obsidian base (#131319), hot pink (#ff46a0), amber (#ff9800), system green (#69df54)
- **Typography** -- Plus Jakarta Sans headlines, IBM Plex Mono data readouts, ALL-CAPS etched labels

---

## Requirements

- Python 3.12+
- FastAPI + Uvicorn (backend)
- Streamlit 1.30+ (frontend)
- Plotly (charts)
- Anthropic SDK (optional, for Claude-powered NL queries -- falls back to keyword matching)

---

## License

Hackathon project -- Micron @ AISG National AI Student Challenge 2025.
