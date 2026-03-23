"""
Trend analysis for semiconductor equipment sensor parameters.

Computes moving averages, trend direction via linear regression,
drift detection, and basic periodic pattern detection -- all using
only the Python standard library.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrendResult:
    """Analysis result for a single sensor parameter."""

    parameter: str
    direction: str  # "increasing", "decreasing", "stable"
    slope: float  # linear regression slope
    r_squared: float  # goodness of fit
    drift_pct: float  # % drift from baseline
    moving_averages: dict[int, list[float]]  # window_size -> values


class TrendAnalyzer:
    """Analyze trends over time for sensor parameters.

    Works entirely with ``list[dict]`` records and stdlib maths.
    """

    DEFAULT_WINDOWS = (5, 10, 20)
    STABLE_THRESHOLD = 0.01  # slope magnitude below this => "stable"

    def __init__(
        self,
        windows: tuple[int, ...] | None = None,
        baseline_fraction: float = 0.3,
        stable_threshold: float | None = None,
    ) -> None:
        self.windows = windows or self.DEFAULT_WINDOWS
        self.baseline_fraction = baseline_fraction
        if stable_threshold is not None:
            self.STABLE_THRESHOLD = stable_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, records: list[dict], parameter: str) -> TrendResult:
        """Analyze a single *parameter* across all *records*."""
        values = self._extract_series(records, parameter)
        return self._analyze_series(values, parameter)

    def analyze_all(
        self,
        records: list[dict],
        parameters: list[str] | None = None,
    ) -> dict[str, TrendResult]:
        """Analyze every requested parameter (or all numeric ones)."""
        if not records:
            return {}
        parameters = parameters or self._infer_parameters(records)
        return {p: self.analyze(records, p) for p in parameters}

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    def _analyze_series(
        self,
        values: list[float],
        parameter: str,
    ) -> TrendResult:
        if not values:
            return TrendResult(
                parameter=parameter,
                direction="stable",
                slope=0.0,
                r_squared=0.0,
                drift_pct=0.0,
                moving_averages={},
            )

        # Moving averages
        ma: dict[int, list[float]] = {}
        for w in self.windows:
            ma[w] = self._moving_average(values, w)

        # Linear regression (index-based x)
        slope, r_sq = self._linear_regression(values)

        # Normalise slope by the mean so the stable threshold is relative.
        mean_val = statistics.mean(values) if values else 1.0
        norm_slope = slope / abs(mean_val) if mean_val != 0 else slope

        if abs(norm_slope) < self.STABLE_THRESHOLD:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Drift detection
        drift_pct = self._compute_drift(values)

        return TrendResult(
            parameter=parameter,
            direction=direction,
            slope=round(slope, 6),
            r_squared=round(r_sq, 6),
            drift_pct=round(drift_pct, 4),
            moving_averages=ma,
        )

    # ------------------------------------------------------------------
    # Moving average
    # ------------------------------------------------------------------

    @staticmethod
    def _moving_average(values: list[float], window: int) -> list[float]:
        """Simple moving average.  Returns a list shorter by *window - 1*."""
        if len(values) < window or window < 1:
            return []
        result: list[float] = []
        running = sum(values[:window])
        result.append(running / window)
        for i in range(window, len(values)):
            running += values[i] - values[i - window]
            result.append(running / window)
        return [round(v, 6) for v in result]

    # ------------------------------------------------------------------
    # Linear regression (ordinary least squares)
    # ------------------------------------------------------------------

    @staticmethod
    def _linear_regression(values: list[float]) -> tuple[float, float]:
        """Return ``(slope, r_squared)`` for *values* indexed by position."""
        n = len(values)
        if n < 2:
            return (0.0, 0.0)

        x_mean = (n - 1) / 2.0
        y_mean = statistics.mean(values)

        ss_xy = 0.0
        ss_xx = 0.0
        ss_yy = 0.0
        for i, y in enumerate(values):
            dx = i - x_mean
            dy = y - y_mean
            ss_xy += dx * dy
            ss_xx += dx * dx
            ss_yy += dy * dy

        if ss_xx == 0:
            return (0.0, 0.0)

        slope = ss_xy / ss_xx
        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy != 0 else 0.0
        return (slope, r_squared)

    # ------------------------------------------------------------------
    # Drift detection
    # ------------------------------------------------------------------

    def _compute_drift(self, values: list[float]) -> float:
        """Percentage drift of recent readings vs historical baseline."""
        if len(values) < 4:
            return 0.0

        split = max(1, int(len(values) * self.baseline_fraction))
        baseline = values[:split]
        recent = values[split:]

        if not baseline or not recent:
            return 0.0

        base_mean = statistics.mean(baseline)
        recent_mean = statistics.mean(recent)

        if base_mean == 0:
            return 0.0 if recent_mean == 0 else 100.0

        return ((recent_mean - base_mean) / abs(base_mean)) * 100.0

    # ------------------------------------------------------------------
    # Autocorrelation (basic periodic pattern detection)
    # ------------------------------------------------------------------

    @staticmethod
    def autocorrelation(values: list[float], max_lag: int | None = None) -> list[float]:
        """Compute autocorrelation for lags 1..max_lag.

        Returns a list where index ``i`` is the autocorrelation at lag
        ``i + 1``.  This is exposed as a static helper; callers can use
        it to look for cyclic behaviour (peaks in the autocorrelation
        indicate periodic patterns).
        """
        n = len(values)
        if n < 4:
            return []
        if max_lag is None:
            max_lag = min(n // 2, 50)

        mean = statistics.mean(values)
        var = sum((v - mean) ** 2 for v in values)
        if var == 0:
            return [0.0] * max_lag

        result: list[float] = []
        for lag in range(1, max_lag + 1):
            cov = sum(
                (values[i] - mean) * (values[i + lag] - mean)
                for i in range(n - lag)
            )
            result.append(round(cov / var, 6))
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_parameters(records: list[dict]) -> list[str]:
        skip = {"timestamp", "record_id", "tool_id", "alarm", "fault", "event"}
        return [
            k
            for k, v in records[0].items()
            if k.lower() not in skip and isinstance(v, (int, float))
        ]

    @staticmethod
    def _extract_series(records: list[dict], parameter: str) -> list[float]:
        """Extract numeric values for *parameter*, ordered by timestamp."""
        pairs: list[tuple[datetime, float]] = []
        for rec in records:
            ts = rec.get("timestamp")
            val = rec.get(parameter)
            if ts is None or val is None:
                continue
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            if not isinstance(val, (int, float)):
                continue
            pairs.append((ts, float(val)))
        pairs.sort(key=lambda t: t[0])
        return [v for _, v in pairs]
