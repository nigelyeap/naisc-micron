"""
Anomaly detection for parsed semiconductor equipment log data.

Supports Z-score, IQR, rate-of-change, and missing-data detection
using only the Python standard library.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Anomaly:
    """A single anomalous reading detected in log data."""

    record_id: str
    timestamp: datetime
    parameter: str  # e.g. "temperature_c"
    value: float
    expected_range: tuple[float, float]
    anomaly_type: str  # "z_score", "iqr", "rate_of_change", "missing_data"
    severity: str  # "LOW", "MEDIUM", "HIGH"
    z_score: float | None
    description: str


class AnomalyDetector:
    """Detect anomalous readings in parsed log data.

    All methods work with plain ``list[dict]`` records so no external
    libraries are required.
    """

    def __init__(
        self,
        z_threshold_medium: float = 2.0,
        z_threshold_high: float = 3.0,
        iqr_multiplier: float = 1.5,
        rate_of_change_pct: float = 20.0,
        expected_interval_seconds: float | None = None,
        missing_data_factor: float = 3.0,
    ) -> None:
        self.z_threshold_medium = z_threshold_medium
        self.z_threshold_high = z_threshold_high
        self.iqr_multiplier = iqr_multiplier
        self.rate_of_change_pct = rate_of_change_pct
        self.expected_interval_seconds = expected_interval_seconds
        self.missing_data_factor = missing_data_factor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        records: list[dict],
        parameters: list[str] | None = None,
    ) -> list[Anomaly]:
        """Run all detection methods across every requested parameter.

        Each *record* dict is expected to have at least ``"timestamp"``
        (a ``datetime`` or ISO-format string) and one or more numeric
        parameter fields.  An optional ``"record_id"`` field is used if
        present; otherwise an index-based ID is generated.

        If *parameters* is ``None``, every numeric field found in the
        first record (excluding ``"timestamp"`` and ``"record_id"``) is
        analysed.
        """
        if not records:
            return []

        parameters = parameters or self._infer_parameters(records)
        all_anomalies: list[Anomaly] = []

        for param in parameters:
            values = self._extract_values(records, param)
            if not values:
                continue
            all_anomalies.extend(self.detect_for_parameter(values, param))

        # Sort by timestamp for readability.
        all_anomalies.sort(key=lambda a: a.timestamp)
        return all_anomalies

    def detect_for_parameter(
        self,
        values: list[tuple[datetime, float, str]],
        param_name: str,
    ) -> list[Anomaly]:
        """Run all detection methods on a single parameter series.

        *values* is a list of ``(timestamp, value, record_id)`` tuples,
        already sorted by timestamp.
        """
        if not values:
            return []

        anomalies: list[Anomaly] = []
        anomalies.extend(self._detect_z_score(values, param_name))
        anomalies.extend(self._detect_iqr(values, param_name))
        anomalies.extend(self._detect_rate_of_change(values, param_name))
        anomalies.extend(self._detect_missing_data(values, param_name))
        return anomalies

    # ------------------------------------------------------------------
    # Z-Score detection
    # ------------------------------------------------------------------

    def _detect_z_score(
        self,
        values: list[tuple[datetime, float, str]],
        param_name: str,
    ) -> list[Anomaly]:
        nums = [v for _, v, _ in values]
        if len(nums) < 2:
            return []

        mean = statistics.mean(nums)
        stdev = statistics.pstdev(nums)
        if stdev == 0:
            return []

        anomalies: list[Anomaly] = []
        lo_med = mean - self.z_threshold_medium * stdev
        hi_med = mean + self.z_threshold_medium * stdev

        for ts, val, rid in values:
            z = (val - mean) / stdev
            abs_z = abs(z)
            if abs_z >= self.z_threshold_medium:
                severity = "HIGH" if abs_z >= self.z_threshold_high else "MEDIUM"
                anomalies.append(
                    Anomaly(
                        record_id=rid,
                        timestamp=ts,
                        parameter=param_name,
                        value=val,
                        expected_range=(lo_med, hi_med),
                        anomaly_type="z_score",
                        severity=severity,
                        z_score=round(z, 4),
                        description=(
                            f"{param_name} value {val} is {abs_z:.2f} standard "
                            f"deviations from the mean ({mean:.4f})"
                        ),
                    )
                )
        return anomalies

    # ------------------------------------------------------------------
    # IQR detection
    # ------------------------------------------------------------------

    def _detect_iqr(
        self,
        values: list[tuple[datetime, float, str]],
        param_name: str,
    ) -> list[Anomaly]:
        nums = sorted(v for _, v, _ in values)
        n = len(nums)
        if n < 4:
            return []

        q1 = self._percentile(nums, 25)
        q3 = self._percentile(nums, 75)
        iqr = q3 - q1
        if iqr == 0:
            return []

        lower = q1 - self.iqr_multiplier * iqr
        upper = q3 + self.iqr_multiplier * iqr

        anomalies: list[Anomaly] = []
        for ts, val, rid in values:
            if val < lower or val > upper:
                distance = max(lower - val, val - upper)
                severity = "HIGH" if distance > 2 * self.iqr_multiplier * iqr else "MEDIUM"
                anomalies.append(
                    Anomaly(
                        record_id=rid,
                        timestamp=ts,
                        parameter=param_name,
                        value=val,
                        expected_range=(lower, upper),
                        anomaly_type="iqr",
                        severity=severity,
                        z_score=None,
                        description=(
                            f"{param_name} value {val} is outside the IQR fence "
                            f"[{lower:.4f}, {upper:.4f}]"
                        ),
                    )
                )
        return anomalies

    # ------------------------------------------------------------------
    # Rate-of-change detection
    # ------------------------------------------------------------------

    def _detect_rate_of_change(
        self,
        values: list[tuple[datetime, float, str]],
        param_name: str,
    ) -> list[Anomaly]:
        if len(values) < 2:
            return []

        anomalies: list[Anomaly] = []
        for i in range(1, len(values)):
            ts_prev, val_prev, _ = values[i - 1]
            ts_curr, val_curr, rid = values[i]

            base = abs(val_prev) if val_prev != 0 else 1.0
            pct_change = abs(val_curr - val_prev) / base * 100.0

            if pct_change >= self.rate_of_change_pct:
                severity = (
                    "HIGH"
                    if pct_change >= self.rate_of_change_pct * 2
                    else "MEDIUM"
                    if pct_change >= self.rate_of_change_pct * 1.5
                    else "LOW"
                )
                anomalies.append(
                    Anomaly(
                        record_id=rid,
                        timestamp=ts_curr,
                        parameter=param_name,
                        value=val_curr,
                        expected_range=(
                            val_prev * (1 - self.rate_of_change_pct / 100),
                            val_prev * (1 + self.rate_of_change_pct / 100),
                        ),
                        anomaly_type="rate_of_change",
                        severity=severity,
                        z_score=None,
                        description=(
                            f"{param_name} changed {pct_change:.1f}% from "
                            f"{val_prev} to {val_curr} between "
                            f"{ts_prev.isoformat()} and {ts_curr.isoformat()}"
                        ),
                    )
                )
        return anomalies

    # ------------------------------------------------------------------
    # Missing-data detection
    # ------------------------------------------------------------------

    def _detect_missing_data(
        self,
        values: list[tuple[datetime, float, str]],
        param_name: str,
    ) -> list[Anomaly]:
        if len(values) < 3:
            return []

        # Estimate expected interval from the median gap if not provided.
        gaps = [
            (values[i][0] - values[i - 1][0]).total_seconds()
            for i in range(1, len(values))
        ]
        if not gaps:
            return []

        if self.expected_interval_seconds is not None:
            expected = self.expected_interval_seconds
        else:
            expected = statistics.median(gaps)

        if expected <= 0:
            return []

        threshold = expected * self.missing_data_factor
        anomalies: list[Anomaly] = []

        for i in range(1, len(values)):
            gap = (values[i][0] - values[i - 1][0]).total_seconds()
            if gap > threshold:
                missed = int(gap / expected) - 1
                anomalies.append(
                    Anomaly(
                        record_id=values[i][2],
                        timestamp=values[i][0],
                        parameter=param_name,
                        value=values[i][1],
                        expected_range=(0, expected),
                        anomaly_type="missing_data",
                        severity="HIGH" if missed > 5 else "MEDIUM" if missed > 2 else "LOW",
                        z_score=None,
                        description=(
                            f"Gap of {gap:.0f}s detected for {param_name} "
                            f"(expected ~{expected:.0f}s). Approximately "
                            f"{missed} reading(s) may be missing."
                        ),
                    )
                )
        return anomalies

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_parameters(records: list[dict]) -> list[str]:
        """Return numeric field names from the first record."""
        skip = {"timestamp", "record_id", "tool_id", "alarm", "fault", "event"}
        params: list[str] = []
        for key, val in records[0].items():
            if key.lower() in skip:
                continue
            if isinstance(val, (int, float)):
                params.append(key)
        return params

    @staticmethod
    def _extract_values(
        records: list[dict],
        param: str,
    ) -> list[tuple[datetime, float, str]]:
        """Pull ``(timestamp, value, record_id)`` tuples for *param*."""
        result: list[tuple[datetime, float, str]] = []
        for idx, rec in enumerate(records):
            ts = rec.get("timestamp")
            val = rec.get(param)
            if ts is None or val is None:
                continue
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            if not isinstance(val, (int, float)):
                continue
            rid = rec.get("record_id", f"rec-{idx}")
            result.append((ts, float(val), str(rid)))
        result.sort(key=lambda t: t[0])
        return result

    @staticmethod
    def _percentile(sorted_data: list[float], pct: float) -> float:
        """Linear-interpolation percentile on already-sorted data."""
        n = len(sorted_data)
        k = (pct / 100) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])
