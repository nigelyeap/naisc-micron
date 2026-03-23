"""
Wrapper around requests for calling the Smart Log Parser backend API.
All methods return parsed JSON or sensible defaults on failure.
"""

from __future__ import annotations

from typing import Any

import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 15  # seconds


class APIClient:
    """Thin HTTP client for the log-parser backend."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------ #
    #  Upload
    # ------------------------------------------------------------------ #
    def upload_file(self, file) -> dict:
        """POST a file object to /api/upload and return the JSON response."""
        name = getattr(file, "name", "upload.log")
        data = file.read() if hasattr(file, "read") else file.getvalue()
        resp = requests.post(
            f"{self.base_url}/api/upload",
            files={"file": (name, data, "application/octet-stream")},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Files & Records
    # ------------------------------------------------------------------ #
    def get_files(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/api/files", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def get_records(self, filters: dict | None = None) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/api/records",
            params=filters or {},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Anomalies
    # ------------------------------------------------------------------ #
    def get_anomalies(self, filters: dict | None = None) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/api/anomalies",
            params=filters or {},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Analytics
    # ------------------------------------------------------------------ #
    def get_summary(self) -> dict:
        resp = requests.get(
            f"{self.base_url}/api/analytics/summary", timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    def get_timeseries(
        self, parameter: str, tool_id: str | None = None
    ) -> list[dict]:
        params: dict[str, Any] = {"parameter": parameter}
        if tool_id:
            params["tool_id"] = tool_id
        resp = requests.get(
            f"{self.base_url}/api/analytics/timeseries",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        # The backend wraps timeseries in {"parameter":..., "data": [...]}
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    def get_cross_tool(self, parameter: str | None = None) -> dict:
        params = {}
        if parameter:
            params["parameter"] = parameter
        resp = requests.get(
            f"{self.base_url}/api/analytics/cross-tool",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Natural Language Query
    # ------------------------------------------------------------------ #
    def nl_query(self, question: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/api/query",
            json={"question": question},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Health
    # ------------------------------------------------------------------ #
    def health_check(self) -> bool:
        """Return True if the backend responds to the health endpoint."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/health", timeout=5
            )
            return resp.status_code == 200
        except requests.ConnectionError:
            return False
        except Exception:
            return False
