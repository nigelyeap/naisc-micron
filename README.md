# Smart Tool Log Parser (SLP)

**Micron @ AISG National AI Student Challenge**

An AI-powered semiconductor equipment log parser that ingests diverse log formats, normalises them into a unified schema, detects anomalies, and provides interactive analytics through a dark-themed React dashboard.

---

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Generate synthetic sample logs (if not already present)
python sample_logs/gen_all.py

# Run everything (backend + frontend together)
python run.py
```

- **Backend API**: http://localhost:8000
- **Dashboard**: http://localhost:5173

Start them separately if needed:

```bash
python run.py --backend   # FastAPI only
python run.py --frontend  # Vite dev server only
```

---

## What It Does

1. **Ingests** semiconductor equipment logs in 8 formats (JSON, XML, CSV, Syslog, Key-Value, plain text, binary, Parquet)
2. **Detects format** automatically by inspecting file content — no file extension required
3. **Parses** each format with a dedicated parser (recursive JSON flattening, XML ElementTree, RFC 3164/5424 syslog, regex KV, hex-dump binary)
4. **Tokenizes** parsed content — segments raw fields into discrete typed tokens (timestamp, key, value, event type) before schema mapping
5. **Infers schema** — maps vendor-specific field names to a unified `UnifiedLogRecord` (timestamp, tool_id, module_id, event_type, severity, parameters, confidence)
6. **Normalises** every record into a consistent structure regardless of source format
7. **Detects anomalies** using Z-score, IQR, rate-of-change, and missing-data methods
8. **Analyses trends** with linear regression, moving averages, and drift detection
9. **Correlates faults** by linking alarm events to preceding sensor anomalies within a time window
10. **Compares tools** across a fleet to identify outlier equipment
11. **Generates summaries** in plain-English markdown
12. **Answers natural language questions** — converts English to SQL via the Claude API, with keyword fallback

---

## Submission Deliverables

### 1. Architecture & Pipeline Flow

The in-app **Architecture** page (sidebar → Architecture icon) provides a detailed interactive pipeline diagram covering every stage:

```
Raw Log Files → Format Detector → Parser → Tokenizer → Schema Inferencer → Normalizer → SQLite DB → FastAPI → React UI
```

Full pipeline breakdown:

| Stage | Description |
|-------|-------------|
| **Log File Ingestion** | Upload via dashboard or POST to `/api/upload`; multi-format accepted |
| **Format Detection** | Content-based: byte patterns, regex heuristics, statistical analysis — no extension needed |
| **Parsing** | 8 dedicated parsers: JSON (recursive), XML, CSV, Syslog, KV, Text, Binary (hex dump), Parquet |
| **Tokenizing** | Segments parsed output into discrete typed tokens: timestamps, event keys, parameter values, severity labels |
| **Normalizing** | Schema inferencer maps vendor fields → unified schema; normalizer produces `UnifiedLogRecord` |
| **Storage** | SQLite (WAL mode, thread-safe): `log_files`, `log_records`, `anomalies` tables |
| **Query & Analysis** | 13 REST endpoints; NL query converts English → SQL; anomaly/trend/fault engines run on stored records |

### 2. Supported Log Formats

| Format | Type | Parser | Sample File |
|--------|------|--------|-------------|
| **JSON** | Structured | Recursive nested flattening | `vendor_a_sensor_trace.json`, `vendor_b_sensor_trace.json` |
| **XML** | Structured | ElementTree extraction | `euv_dose_recipe.xml` |
| **CSV** | Structured | Header inference + row parsing | `sensor_readings.csv` |
| **Syslog** | Semi-structured | RFC 3164 / 5424 parsing | `syslog_equipment.log` |
| **Key-Value** | Semi-structured | Regex `key=value` extraction | `kv_process_log.log` |
| **Plain Text** | Unstructured | Pattern matching for dates, IDs, events | `event_log.txt` |
| **Binary** | Unstructured | Hex dump + embedded string extraction | `binary_diagnostic.bin` |
| **Parquet** | Structured (binary) | Apache Arrow columnar read via pyarrow | `vendor_c_sensor_trace.parquet` |

Format detection is **content-based** — the detector inspects byte patterns, structure markers, and statistical properties to classify each file independently of its extension.

### 3. Features, Functionalities & Constraints

#### Features
- Multi-format log ingestion with automatic format detection
- Unified schema normalisation across all 8 input formats
- Real-time anomaly detection (Z-score, IQR, rate-of-change, missing data)
- Trend analysis (linear regression, moving averages, drift detection)
- Cross-tool fleet comparison with outlier detection
- Natural language querying (English → SQL) via Claude API with keyword fallback
- Plain-English summary report generation
- Fault correlation linking alarms to preceding anomalies

#### Dashboard Pages
| Page | Description |
|------|-------------|
| **Overview** | KPI cards, severity/event/tool charts, recent events feed, ingested files panel |
| **Upload** | Drag-and-drop or file-select upload; shows parse results, record count, confidence |
| **Explorer** | Filterable, paginated table of all parsed records with expandable detail rows |
| **Analytics** | Timeseries, anomaly, trend, and cross-tool comparison charts |
| **NL Query** | Natural language query input with SQL preview and dynamic results table |
| **Summary** | AI-generated markdown report with export to `.md` |
| **Architecture** | Interactive pipeline diagram + component reference table |

#### Constraints
- Requires Python 3.12+ and Node.js 18+
- Claude API key optional — NL query falls back to keyword matching if `ANTHROPIC_API_KEY` is not set
- Binary parser extracts printable strings and hex patterns only; proprietary vendor binary formats may require vendor tools for full decoding
- Database is local SQLite; not designed for concurrent multi-user write load

#### a) Development Tools

| Tool | Purpose |
|------|---------|
| **Python 3.12** | Backend language |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **SQLite** | Embedded database (WAL mode, thread-safe) |
| **React 19 + TypeScript** | Frontend framework |
| **Vite** | Frontend build tool and dev server |
| **TailwindCSS** | Utility-first CSS styling |
| **shadcn/ui** | Accessible UI component library |
| **Recharts** | Chart and data visualisation library |
| **TanStack Query v5** | Server state management and request caching |
| **React Router v7** | Client-side routing |
| **Lucide React** | SVG icon set |
| **Axios** | HTTP client for API requests |

#### b) APIs Used

| API | Usage |
|-----|-------|
| **Anthropic Claude API** (`claude-sonnet-4-6`) | Natural language → SQL conversion in the NL Query page; LLM fallback parser for unrecognised log formats |
| **Internal FastAPI REST API** | All communication between the React frontend and the Python backend (13 endpoints at `http://localhost:8000/api/`) |

#### c) Assets Used

| Asset | Source | Usage |
|-------|--------|-------|
| **Synthetic log samples** | Generated via `sample_logs/gen_all.py` | 9 demo files covering all 8 supported formats |
| **Bunny Fonts** — Fira Sans, Fira Code | bunny.net/fonts | Dashboard typography (body + monospace) |
| **Lucide React icons** | lucide.dev | Sidebar navigation and UI icons |

### 4. Functioning Prototype

Run `python run.py` then open http://localhost:5173. The dashboard demonstrates:
- Uploading and parsing each of the 9 synthetic log files across all 8 formats
- Anomaly detection results visible in the Analytics page
- Natural language query (e.g. `show all critical events from tool ETCH_001`)
- Auto-generated plain-English summary report with markdown export

---

## Project Structure

```
NAISC Micron/
├── run.py                    # Central launcher (backend + frontend)
├── test_app.py               # End-to-end test suite (123 tests)
├── requirements.txt
│
├── parser/                   # Core parsing engine
│   ├── format_detector.py    # Content-based format detection
│   ├── pipeline.py           # Orchestrator: detect → parse → tokenize → normalize
│   ├── schema_inferencer.py  # Maps vendor fields to unified schema
│   ├── normalizer.py         # Produces UnifiedLogRecord dicts
│   ├── llm_fallback.py       # Claude API fallback for unknown formats
│   └── parsers/
│       ├── json_parser.py    # Recursive nested JSON flattening
│       ├── xml_parser.py     # ElementTree-based extraction
│       ├── csv_parser.py     # Standard CSV with header inference
│       ├── syslog_parser.py  # RFC 3164/5424 parsing
│       ├── kv_parser.py      # Key=value regex extraction
│       ├── text_parser.py    # Regex-based unstructured text
│       └── binary_parser.py  # Hex dump + embedded string extraction
│
├── analytics/                # Analysis engines
│   ├── anomaly_detector.py   # Z-score, IQR, rate-of-change, missing data
│   ├── trend_analyzer.py     # Linear regression, moving averages, drift
│   ├── fault_correlator.py   # Alarm-to-anomaly time-window correlation
│   ├── cross_tool_comparator.py  # Fleet-wide outlier detection
│   └── summary_generator.py  # Markdown report generation
│
├── backend/                  # FastAPI + SQLite
│   ├── app.py                # 13 REST API endpoints
│   ├── database.py           # Thread-safe SQLite (3 tables, WAL mode)
│   └── nl_query.py           # English → SQL conversion
│
├── frontend/                 # React + Vite dashboard
│   ├── src/
│   │   ├── pages/            # Overview, Upload, Explorer, Analytics, NLQuery, Summary, Architecture
│   │   ├── components/       # Sidebar, TopBar, KpiCard, SeverityBadge, FormatBadge, shadcn/ui
│   │   └── lib/              # API client (axios), utils
│   └── package.json
│
├── sample_logs/              # Synthetic demo data (9 files, all 8 formats)
│   ├── gen_all.py            # Generator script
│   ├── vendor_a_sensor_trace.json
│   ├── vendor_b_sensor_trace.json
│   ├── euv_dose_recipe.xml
│   ├── sensor_readings.csv
│   ├── syslog_equipment.log
│   ├── kv_process_log.log
│   ├── event_log.txt
│   ├── binary_diagnostic.bin
│   └── vendor_c_sensor_trace.parquet
│
└── data/
    └── logs.db               # SQLite database (auto-created on first run)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload and parse a log file |
| `GET` | `/api/files` | List all uploaded files |
| `GET` | `/api/samples` | List available sample log files |
| `POST` | `/api/samples/upload/{filename}` | Parse a built-in sample log |
| `GET` | `/api/records` | Query records (filters: tool_id, event_type, severity, source_format, file_id) |
| `GET` | `/api/records/{id}` | Get single record |
| `GET` | `/api/anomalies` | Query detected anomalies |
| `GET` | `/api/analytics/summary` | Overall statistics |
| `GET` | `/api/analytics/timeseries` | Parameter timeseries data |
| `GET` | `/api/analytics/trends` | Trend analysis for a parameter |
| `GET` | `/api/analytics/cross-tool` | Cross-tool comparison |
| `POST` | `/api/query` | Natural language query (English → SQL) |

---

## Database Schema

**3 tables in SQLite (WAL mode, thread-safe):**

**`log_files`** — Uploaded file metadata
- `id`, `filename`, `format_detected`, `upload_time`, `total_records`, `avg_confidence`, `parse_time_ms`

**`log_records`** — Parsed and normalised records
- `id`, `file_id` (FK), `source_format`, `timestamp`, `tool_id`, `module_id`, `event_type`, `severity`, `parameters_json`, `raw_content`, `confidence`, `parse_warnings_json`

**`anomalies`** — Detected anomalies
- `id`, `record_id`, `parameter`, `value`, `expected_min`, `expected_max`, `anomaly_type`, `severity`, `z_score`, `description`, `detected_at`

---

## Testing

```bash
python test_app.py
```

123 tests across 14 sections covering format detection, all parsers, schema inference, full pipeline, anomaly detection, trend analysis, cross-tool comparison, fault correlation, summary generation, database operations, NL query, API endpoints, and edge cases.

---

## Requirements

- Python 3.12+
- Node.js 18+
- Anthropic API key (optional — set as `ANTHROPIC_API_KEY` env var; NL query falls back to keyword matching without it)

---

## License

Hackathon project — Micron @ AISG National AI Student Challenge 2025.
