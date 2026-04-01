"""
Natural language query engine.

Converts plain-English questions about semiconductor equipment logs
into SQL queries, executes them, and returns human-readable answers.
Uses the Anthropic Claude API when available; falls back to simple
keyword-based mapping otherwise.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from backend.database import Database


@dataclass
class NLQueryResult:
    """Container for a natural-language query response."""

    generated_sql: str
    results: list[dict]
    explanation: str
    confidence: float


# ---------------------------------------------------------------------------
# Schema description fed to the LLM
# ---------------------------------------------------------------------------

_SCHEMA_DESCRIPTION = """\
SQLite database with three tables:

1. log_files
   - id (INTEGER PK), filename (TEXT), format_detected (TEXT),
     upload_time (TEXT ISO-8601), total_records (INTEGER),
     avg_confidence (REAL), parse_time_ms (REAL)

2. log_records
   - id (INTEGER PK), file_id (INTEGER FK -> log_files.id),
     source_format (TEXT), timestamp (TEXT ISO-8601),
     tool_id (TEXT), module_id (TEXT), event_type (TEXT),
     severity (TEXT), parameters_json (TEXT -- JSON dict),
     raw_content (TEXT), confidence (REAL),
     parse_warnings_json (TEXT -- JSON list)

3. anomalies
   - id (INTEGER PK), record_id (TEXT),
     parameter (TEXT), value (REAL), expected_min (REAL),
     expected_max (REAL), anomaly_type (TEXT), severity (TEXT),
     z_score (REAL), description (TEXT),
     detected_at (TEXT ISO-8601)

Common event_type values: SENSOR_READ, ALARM, EVENT, RECIPE, WAFER_OP, UNKNOWN
Common severity values: INFO, WARNING, ERROR, CRITICAL
"""


class NLQueryEngine:
    """Translate natural-language questions into SQL and run them."""

    def __init__(self, db: Database, api_key: str | None = None):
        self.db = db
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

        if self.api_key:
            try:
                import anthropic  # noqa: F401

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                self._client = None

    # -- public API -----------------------------------------------------------

    def query(self, question: str) -> NLQueryResult:
        """Answer *question* by converting it to SQL, executing, and explaining."""
        if self._client is not None:
            return self._query_with_llm(question)
        return self._query_with_fallback(question)

    # -- LLM path -------------------------------------------------------------

    def _query_with_llm(self, question: str) -> NLQueryResult:
        prompt = self._build_prompt(question)

        response = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_reply = response.content[0].text

        # Extract SQL from the response (expect it in a ```sql block or bare)
        sql = self._extract_sql(raw_reply)
        if not sql or not self._validate_sql(sql):
            return NLQueryResult(
                generated_sql=sql or "",
                results=[],
                explanation="Could not generate a safe SQL query for that question.",
                confidence=0.0,
            )

        try:
            results = self.db.execute_sql(sql)
        except Exception as exc:
            return NLQueryResult(
                generated_sql=sql,
                results=[],
                explanation=f"Query failed: {exc}",
                confidence=0.2,
            )

        # Ask the LLM to summarise the results
        explanation = self._explain_results(question, sql, results)

        return NLQueryResult(
            generated_sql=sql,
            results=results,
            explanation=explanation,
            confidence=0.85,
        )

    def _build_prompt(self, question: str) -> str:
        return (
            "You are a SQL expert. Given the database schema below and a "
            "user's natural-language question, produce ONLY a single SQLite "
            "SELECT statement that answers the question. Do NOT include any "
            "INSERT, UPDATE, DELETE, DROP, or other mutation statements.\n\n"
            f"### Schema\n{_SCHEMA_DESCRIPTION}\n"
            f"### Question\n{question}\n\n"
            "Respond with ONLY the SQL query inside a ```sql code block."
        )

    def _extract_sql(self, text: str) -> str | None:
        """Pull SQL from a ```sql ... ``` block, or treat the whole text as SQL."""
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback: try the entire response if it looks like SQL
        stripped = text.strip().rstrip(";").strip()
        if stripped.upper().startswith("SELECT"):
            return stripped
        return None

    def _validate_sql(self, sql: str) -> bool:
        """Only allow SELECT statements; block mutations."""
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned.upper().startswith("SELECT"):
            return False
        disallowed = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "ATTACH"}
        tokens = cleaned.upper().split()
        return not any(t in disallowed for t in tokens)

    def _explain_results(
        self, question: str, sql: str, results: list[dict]
    ) -> str:
        """Use the LLM to produce a short human-readable answer."""
        if not results:
            return "No results found."

        # Truncate to avoid huge prompts
        preview = str(results[:20])
        if len(preview) > 2000:
            preview = preview[:2000] + "..."

        prompt = (
            "Given this question, the SQL query used, and the results, "
            "write a short (2-3 sentence) plain-English answer.\n\n"
            f"Question: {question}\n"
            f"SQL: {sql}\n"
            f"Results (first 20 rows): {preview}\n\n"
            "Answer concisely:"
        )
        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception:
            return f"Found {len(results)} result(s)."

    # -- keyword fallback path ------------------------------------------------

    def _query_with_fallback(self, question: str) -> NLQueryResult:
        """Basic keyword-to-SQL mapping when no API key is available."""
        q = question.lower()
        sql = ""
        explanation = ""

        if any(w in q for w in ("alarm", "alarms")):
            sql = "SELECT * FROM log_records WHERE event_type = 'ALARM' ORDER BY timestamp DESC LIMIT 50"
            explanation = "Showing the most recent alarm events."

        elif any(w in q for w in ("error", "errors")):
            sql = "SELECT * FROM log_records WHERE severity = 'ERROR' ORDER BY timestamp DESC LIMIT 50"
            explanation = "Showing the most recent error events."

        elif any(w in q for w in ("warning", "warnings")):
            sql = "SELECT * FROM log_records WHERE severity = 'WARNING' ORDER BY timestamp DESC LIMIT 50"
            explanation = "Showing the most recent warning events."

        elif "anomal" in q:
            sql = "SELECT * FROM anomalies ORDER BY detected_at DESC LIMIT 50"
            explanation = "Showing the most recent anomalies."

        elif "summary" in q or "overview" in q:
            sql = (
                "SELECT event_type, severity, COUNT(*) as cnt "
                "FROM log_records GROUP BY event_type, severity "
                "ORDER BY cnt DESC"
            )
            explanation = "Summary of events grouped by type and severity."

        elif "tool" in q and ("most" in q or "top" in q):
            sql = (
                "SELECT tool_id, COUNT(*) as cnt FROM log_records "
                "WHERE tool_id IS NOT NULL GROUP BY tool_id ORDER BY cnt DESC LIMIT 10"
            )
            explanation = "Tools ranked by number of log records."

        elif "temperature" in q or "temp" in q:
            sql = (
                "SELECT id, timestamp, tool_id, parameters_json FROM log_records "
                "WHERE parameters_json LIKE '%temperature%' OR parameters_json LIKE '%temp%' "
                "ORDER BY timestamp DESC LIMIT 50"
            )
            explanation = "Records containing temperature parameters."

        elif "vacuum" in q or "pressure" in q:
            sql = (
                "SELECT id, timestamp, tool_id, event_type, parameters_json FROM log_records "
                "WHERE parameters_json LIKE '%vacuum%' OR parameters_json LIKE '%pressure%' "
                "OR raw_content LIKE '%vacuum%' OR raw_content LIKE '%pressure%' "
                "ORDER BY timestamp DESC LIMIT 50"
            )
            explanation = "Records related to vacuum/pressure readings."

        elif "fault" in q:
            sql = (
                "SELECT * FROM log_records WHERE event_type = 'ALARM' "
                "OR severity IN ('ERROR', 'CRITICAL') "
                "ORDER BY timestamp DESC LIMIT 50"
            )
            explanation = "Showing recent fault-related events."

        else:
            # Generic full-text-ish search
            # Extract likely keywords (skip stop words)
            stop = {"show", "me", "all", "the", "in", "a", "an", "what", "which",
                     "how", "many", "is", "are", "was", "were", "get", "find", "list"}
            words = [w for w in re.findall(r"\w+", q) if w not in stop and len(w) > 2]
            if words:
                like_clauses = " OR ".join(
                    f"raw_content LIKE '%{w}%'" for w in words[:5]
                )
                sql = (
                    f"SELECT * FROM log_records WHERE {like_clauses} "
                    "ORDER BY timestamp DESC LIMIT 50"
                )
                explanation = f"Searching records for: {', '.join(words[:5])}"
            else:
                sql = "SELECT * FROM log_records ORDER BY timestamp DESC LIMIT 20"
                explanation = "Showing the 20 most recent records."

        try:
            results = self.db.execute_sql(sql)
        except Exception as exc:
            return NLQueryResult(
                generated_sql=sql,
                results=[],
                explanation=f"Query failed: {exc}",
                confidence=0.1,
            )

        return NLQueryResult(
            generated_sql=sql,
            results=results,
            explanation=explanation,
            confidence=0.5,
        )
