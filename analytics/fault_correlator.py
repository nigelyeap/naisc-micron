"""
Fault correlation engine for semiconductor equipment logs.

Finds relationships between alarm/fault events and sensor readings
by examining time windows around fault occurrences and building a
co-occurrence matrix.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

from analytics.anomaly_detector import Anomaly


@dataclass
class FaultCorrelation:
    """One fault event with its correlated anomalies and context."""

    fault_event: str
    timestamp: datetime
    correlated_anomalies: list[Anomaly]
    preceding_parameters: dict[str, float]  # parameter values just before fault
    likely_cause: str  # best guess based on correlations


class FaultCorrelator:
    """Correlate faults/alarms with sensor anomalies.

    No required constructor arguments -- all tunables have sensible
    defaults.
    """

    def __init__(
        self,
        fault_fields: list[str] | None = None,
    ) -> None:
        # Names of dict keys that indicate a fault/alarm event.
        self.fault_fields = fault_fields or ["alarm", "fault", "event"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def correlate(
        self,
        records: list[dict],
        anomalies: list[Anomaly],
        window_minutes: int = 5,
    ) -> list[FaultCorrelation]:
        """Return a list of fault correlations.

        For every fault/alarm event found in *records*, gather anomalies
        that occurred within *window_minutes* before or after the event,
        and snapshot sensor readings immediately preceding it.
        """
        if not records:
            return []

        fault_events = self._extract_faults(records)
        if not fault_events:
            return []

        window = timedelta(minutes=window_minutes)
        results: list[FaultCorrelation] = []

        for fault_name, fault_ts, fault_idx in fault_events:
            # Anomalies within the window
            corr_anomalies = [
                a
                for a in anomalies
                if abs((a.timestamp - fault_ts).total_seconds()) <= window.total_seconds()
            ]

            # Parameter snapshot just before the fault
            preceding = self._snapshot_preceding(records, fault_idx)

            # Determine likely cause
            cause = self._guess_cause(corr_anomalies, preceding)

            results.append(
                FaultCorrelation(
                    fault_event=fault_name,
                    timestamp=fault_ts,
                    correlated_anomalies=corr_anomalies,
                    preceding_parameters=preceding,
                    likely_cause=cause,
                )
            )

        return results

    def cooccurrence_matrix(
        self,
        correlations: list[FaultCorrelation],
    ) -> dict[str, dict[str, int]]:
        """Build a fault-type co-occurrence matrix.

        Returns ``{fault_a: {fault_b: count}}`` for every pair of
        faults that share at least one anomaly (i.e. anomalies in
        overlapping time windows).
        """
        # Group anomalies by record_id to find shared anomalies.
        fault_by_anomaly: dict[str, list[str]] = {}
        for corr in correlations:
            for anom in corr.correlated_anomalies:
                fault_by_anomaly.setdefault(anom.record_id, []).append(
                    corr.fault_event
                )

        matrix: dict[str, dict[str, int]] = {}
        for faults in fault_by_anomaly.values():
            unique = list(set(faults))
            for i, fa in enumerate(unique):
                for fb in unique[i + 1 :]:
                    matrix.setdefault(fa, {}).setdefault(fb, 0)
                    matrix[fa][fb] += 1
                    matrix.setdefault(fb, {}).setdefault(fa, 0)
                    matrix[fb][fa] += 1

        return matrix

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_faults(
        self,
        records: list[dict],
    ) -> list[tuple[str, datetime, int]]:
        """Return ``(fault_name, timestamp, index)`` for each fault event."""
        faults: list[tuple[str, datetime, int]] = []
        for idx, rec in enumerate(records):
            ts = rec.get("timestamp")
            if ts is None:
                continue
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            for fld in self.fault_fields:
                val = rec.get(fld)
                if val and str(val).strip():
                    faults.append((str(val).strip(), ts, idx))
        return faults

    @staticmethod
    def _snapshot_preceding(
        records: list[dict],
        fault_idx: int,
    ) -> dict[str, float]:
        """Grab numeric parameter values from the record just before the fault."""
        skip = {"timestamp", "record_id", "tool_id", "alarm", "fault", "event"}
        if fault_idx == 0:
            # No preceding record -- use the fault record itself.
            rec = records[0]
        else:
            rec = records[fault_idx - 1]

        snapshot: dict[str, float] = {}
        for k, v in rec.items():
            if k.lower() in skip:
                continue
            if isinstance(v, (int, float)):
                snapshot[k] = float(v)
        return snapshot

    @staticmethod
    def _guess_cause(
        anomalies: list[Anomaly],
        preceding: dict[str, float],
    ) -> str:
        """Heuristic: the most-frequently anomalous parameter is the
        likely cause.  Falls back to a generic message when there are
        no correlated anomalies."""
        if not anomalies:
            return "No correlated anomalies found in the time window"

        counter: Counter[str] = Counter()
        high_severity: list[str] = []
        for a in anomalies:
            counter[a.parameter] += 1
            if a.severity == "high":
                high_severity.append(a.parameter)

        # Prefer high-severity parameters.
        if high_severity:
            top = Counter(high_severity).most_common(1)[0][0]
        else:
            top = counter.most_common(1)[0][0]

        count = counter[top]
        return (
            f"Parameter '{top}' showed {count} anomal{'y' if count == 1 else 'ies'} "
            f"around the fault event"
        )
