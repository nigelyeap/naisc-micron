"""
SQLite database layer for storing parsed log records, file metadata,
and detected anomalies.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "logs.db",
)


class Database:
    """Thread-safe SQLite wrapper for the log parser backend."""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        # Make sure the parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self.init_tables()

    # -- connection management ------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return a per-thread connection (created lazily)."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        return conn

    # -- schema ---------------------------------------------------------------

    def init_tables(self) -> None:
        """Create tables if they do not already exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS log_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                filename        TEXT    NOT NULL,
                format_detected TEXT,
                upload_time     TEXT    NOT NULL DEFAULT (datetime('now')),
                total_records   INTEGER DEFAULT 0,
                avg_confidence  REAL    DEFAULT 0.0,
                parse_time_ms   REAL    DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS log_records (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id             INTEGER NOT NULL REFERENCES log_files(id),
                source_format       TEXT,
                timestamp           TEXT,
                tool_id             TEXT,
                module_id           TEXT,
                event_type          TEXT,
                severity            TEXT,
                parameters_json     TEXT,
                raw_content         TEXT,
                confidence          REAL DEFAULT 0.0,
                parse_warnings_json TEXT
            );

            CREATE TABLE IF NOT EXISTS anomalies (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id       TEXT,
                parameter       TEXT,
                value           REAL,
                expected_min    REAL,
                expected_max    REAL,
                anomaly_type    TEXT,
                severity        TEXT,
                z_score         REAL,
                description     TEXT,
                detected_at     TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_records_file    ON log_records(file_id);
            CREATE INDEX IF NOT EXISTS idx_records_tool    ON log_records(tool_id);
            CREATE INDEX IF NOT EXISTS idx_records_event   ON log_records(event_type);
            CREATE INDEX IF NOT EXISTS idx_records_severity ON log_records(severity);
            CREATE INDEX IF NOT EXISTS idx_anomalies_record ON anomalies(record_id);
            """
        )
        conn.commit()

    # -- inserts --------------------------------------------------------------

    def insert_file(
        self,
        filename: str,
        format_detected: str = None,
        total_records: int = 0,
        avg_confidence: float = 0.0,
        parse_time_ms: float = 0.0,
    ) -> int:
        """Insert a log_files row and return its id."""
        conn = self._get_conn()
        cur = conn.execute(
            """
            INSERT INTO log_files (filename, format_detected, upload_time,
                                   total_records, avg_confidence, parse_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                format_detected,
                datetime.now(timezone.utc).isoformat(),
                total_records,
                avg_confidence,
                parse_time_ms,
            ),
        )
        conn.commit()
        return cur.lastrowid

    def insert_records(self, file_id: int, records: list[dict]) -> list[int]:
        """Bulk-insert parsed log records. Returns list of inserted row IDs."""
        if not records:
            return []
        conn = self._get_conn()
        inserted_ids: list[int] = []
        sql = (
            "INSERT INTO log_records"
            "    (file_id, source_format, timestamp, tool_id, module_id,"
            "     event_type, severity, parameters_json, raw_content,"
            "     confidence, parse_warnings_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        for r in records:
            cur = conn.execute(
                sql,
                (
                    file_id,
                    r.get("source_format"),
                    r.get("timestamp"),
                    r.get("tool_id"),
                    r.get("module_id"),
                    r.get("event_type"),
                    r.get("severity"),
                    json.dumps(r.get("parameters", {})) if r.get("parameters") else None,
                    r.get("raw_content"),
                    r.get("confidence", 0.0),
                    json.dumps(r.get("parse_warnings", [])) if r.get("parse_warnings") else None,
                ),
            )
            inserted_ids.append(cur.lastrowid)
        conn.commit()
        return inserted_ids

    def insert_anomalies(self, anomalies: list[dict]) -> None:
        """Bulk-insert detected anomalies."""
        if not anomalies:
            return
        conn = self._get_conn()
        rows = []
        for a in anomalies:
            rows.append(
                (
                    a.get("record_id"),
                    a.get("parameter"),
                    a.get("value"),
                    a.get("expected_min"),
                    a.get("expected_max"),
                    a.get("anomaly_type"),
                    a.get("severity"),
                    a.get("z_score"),
                    a.get("description"),
                    a.get("detected_at", datetime.now(timezone.utc).isoformat()),
                )
            )
        conn.executemany(
            """
            INSERT INTO anomalies
                (record_id, parameter, value, expected_min, expected_max,
                 anomaly_type, severity, z_score, description, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()

    # -- queries --------------------------------------------------------------

    def query_records(
        self,
        filters: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Query log_records with optional filters.

        Supported filter keys: tool_id, event_type, severity, file_id,
        source_format, start_date, end_date.
        """
        clauses: list[str] = []
        params: list[Any] = []
        filters = filters or {}

        for col in ("tool_id", "event_type", "severity", "file_id", "source_format"):
            if col in filters and filters[col] is not None:
                clauses.append(f"{col} = ?")
                params.append(filters[col])

        if "start_date" in filters and filters["start_date"]:
            clauses.append("timestamp >= ?")
            params.append(filters["start_date"])
        if "end_date" in filters and filters["end_date"]:
            clauses.append("timestamp <= ?")
            params.append(filters["end_date"])

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM log_records{where} ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = self._get_conn()
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_record_by_id(self, record_id: int) -> dict | None:
        """Return a single record by id, or None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM log_records WHERE id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def query_anomalies(self, filters: dict | None = None) -> list[dict]:
        """Query anomalies with optional filters.

        Supported filter keys: anomaly_type, severity, parameter, record_id.
        """
        clauses: list[str] = []
        params: list[Any] = []
        filters = filters or {}

        for col in ("anomaly_type", "severity", "parameter", "record_id"):
            if col in filters and filters[col] is not None:
                clauses.append(f"{col} = ?")
                params.append(filters[col])

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM anomalies{where} ORDER BY detected_at DESC"

        conn = self._get_conn()
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_summary_stats(self) -> dict:
        """Return high-level summary statistics across all data."""
        conn = self._get_conn()

        file_count = conn.execute("SELECT COUNT(*) FROM log_files").fetchone()[0]
        record_count = conn.execute("SELECT COUNT(*) FROM log_records").fetchone()[0]
        anomaly_count = conn.execute("SELECT COUNT(*) FROM anomalies").fetchone()[0]

        event_types = conn.execute(
            "SELECT event_type, COUNT(*) as cnt FROM log_records "
            "GROUP BY event_type ORDER BY cnt DESC"
        ).fetchall()

        severity_counts = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM log_records "
            "GROUP BY severity ORDER BY cnt DESC"
        ).fetchall()

        tool_counts = conn.execute(
            "SELECT tool_id, COUNT(*) as cnt FROM log_records "
            "WHERE tool_id IS NOT NULL GROUP BY tool_id ORDER BY cnt DESC"
        ).fetchall()

        avg_confidence = conn.execute(
            "SELECT AVG(confidence) FROM log_records"
        ).fetchone()[0]

        return {
            "total_files": file_count,
            "total_records": record_count,
            "total_anomalies": anomaly_count,
            "avg_confidence": round(avg_confidence, 4) if avg_confidence else 0.0,
            "event_type_breakdown": {r["event_type"]: r["cnt"] for r in event_types},
            "severity_breakdown": {r["severity"]: r["cnt"] for r in severity_counts},
            "tool_breakdown": {r["tool_id"]: r["cnt"] for r in tool_counts},
        }

    def get_parameter_timeseries(
        self, parameter: str, tool_id: str | None = None
    ) -> list[dict]:
        """Extract a timeseries for a given parameter from parameters_json.

        This scans log_records whose parameters_json contains the given
        parameter key, pulling out (timestamp, value) pairs.
        """
        conn = self._get_conn()
        clauses = ["parameters_json LIKE ?"]
        params: list[Any] = [f'%"{parameter}"%']

        if tool_id:
            clauses.append("tool_id = ?")
            params.append(tool_id)

        where = " WHERE " + " AND ".join(clauses)
        sql = (
            f"SELECT id, timestamp, tool_id, parameters_json "
            f"FROM log_records{where} ORDER BY timestamp ASC"
        )
        rows = conn.execute(sql, params).fetchall()

        results: list[dict] = []
        for row in rows:
            try:
                pdata = json.loads(row["parameters_json"]) if row["parameters_json"] else {}
            except (json.JSONDecodeError, TypeError):
                continue
            if parameter in pdata:
                results.append(
                    {
                        "record_id": row["id"],
                        "timestamp": row["timestamp"],
                        "tool_id": row["tool_id"],
                        "parameter": parameter,
                        "value": pdata[parameter],
                    }
                )
        return results

    def get_files(self) -> list[dict]:
        """Return all log_files rows."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM log_files ORDER BY upload_time DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # -- arbitrary SELECT -----------------------------------------------------

    def execute_sql(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute an arbitrary SELECT query safely.

        Only SELECT statements are allowed -- any mutation attempt raises
        a ValueError.
        """
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")

        # Block obvious mutation keywords even inside CTEs / sub-queries
        _DISALLOWED = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "ATTACH"}
        tokens = cleaned.upper().split()
        for token in tokens:
            if token in _DISALLOWED:
                raise ValueError(f"Disallowed SQL keyword: {token}")

        conn = self._get_conn()
        rows = conn.execute(cleaned, params).fetchall()
        return [dict(r) for r in rows]
