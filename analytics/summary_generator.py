"""
Human-readable summary generator for semiconductor log analysis.

Produces markdown-formatted reports from anomaly, trend, fault, and
cross-tool comparison results.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from analytics.anomaly_detector import Anomaly
from analytics.trend_analyzer import TrendResult
from analytics.fault_correlator import FaultCorrelation
from analytics.cross_tool_comparator import ToolComparison


class SummaryGenerator:
    """Generate plain-English markdown summaries of log analysis."""

    def __init__(self) -> None:
        pass

    def summarize_parse_result(
        self,
        records: list[dict],
        anomalies: list[Anomaly],
        trends: dict[str, TrendResult] | None = None,
        faults: list[FaultCorrelation] | None = None,
        comparisons: list[ToolComparison] | None = None,
    ) -> str:
        """Return a complete markdown-formatted analysis summary."""
        trends = trends or {}
        faults = faults or []
        comparisons = comparisons or []

        sections: list[str] = []
        sections.append(self._overview(records, anomalies))
        sections.append(self._anomaly_section(anomalies))
        sections.append(self._alarm_section(records, faults))
        sections.append(self._trend_section(trends))
        sections.append(self._key_findings(anomalies, trends, faults, comparisons))

        return "\n\n".join(s for s in sections if s)

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    def _overview(self, records: list[dict], anomalies: list[Anomaly]) -> str:
        total = len(records)
        tools = self._unique_tools(records)
        tool_count = len(tools)
        ts_min, ts_max = self._time_span(records)

        high_count = sum(1 for a in anomalies if a.severity == "high")

        lines = [
            "## Log Analysis Summary",
            f"- **Total Records**: {total:,} across {tool_count} tool{'s' if tool_count != 1 else ''}",
        ]
        if ts_min and ts_max:
            lines.append(
                f"- **Time Span**: {ts_min.strftime('%Y-%m-%d %H:%M')} to "
                f"{ts_max.strftime('%Y-%m-%d %H:%M')}"
            )
        lines.append(
            f"- **Anomalies Detected**: {len(anomalies)} "
            f"({high_count} high severity)"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Anomaly breakdown
    # ------------------------------------------------------------------

    @staticmethod
    def _anomaly_section(anomalies: list[Anomaly]) -> str:
        if not anomalies:
            return ""
        by_type: Counter[str] = Counter(a.anomaly_type for a in anomalies)
        lines = ["### Anomaly Breakdown"]
        for atype, count in by_type.most_common():
            label = atype.replace("_", " ").title()
            lines.append(f"- {label}: {count}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Alarms / faults
    # ------------------------------------------------------------------

    def _alarm_section(
        self,
        records: list[dict],
        faults: list[FaultCorrelation],
    ) -> str:
        alarm_counter: Counter[str] = Counter()
        for rec in records:
            for fld in ("alarm", "fault", "event"):
                val = rec.get(fld)
                if val and str(val).strip():
                    alarm_counter[str(val).strip()] += 1

        if not alarm_counter:
            return ""

        lines = ["### Active Alarms"]
        for alarm, count in alarm_counter.most_common():
            lines.append(f"- {count} x {alarm}")

        if faults:
            lines.append("")
            lines.append("### Fault Correlations")
            for fc in faults:
                n = len(fc.correlated_anomalies)
                lines.append(
                    f"- **{fc.fault_event}** at {fc.timestamp.strftime('%H:%M:%S')}: "
                    f"{n} correlated anomal{'y' if n == 1 else 'ies'} "
                    f"-- {fc.likely_cause}"
                )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Trends
    # ------------------------------------------------------------------

    @staticmethod
    def _trend_section(trends: dict[str, TrendResult]) -> str:
        if not trends:
            return ""
        non_stable = {k: v for k, v in trends.items() if v.direction != "stable"}
        if not non_stable:
            return "### Trends\nAll monitored parameters are stable."
        lines = ["### Trends"]
        for param, tr in non_stable.items():
            drift = f", drift {tr.drift_pct:+.1f}% from baseline" if abs(tr.drift_pct) > 1 else ""
            lines.append(
                f"- **{param}**: {tr.direction} (R^2={tr.r_squared:.2f}{drift})"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Key findings
    # ------------------------------------------------------------------

    @staticmethod
    def _key_findings(
        anomalies: list[Anomaly],
        trends: dict[str, TrendResult],
        faults: list[FaultCorrelation],
        comparisons: list[ToolComparison],
    ) -> str:
        findings: list[str] = []

        # Drifting parameters
        for param, tr in trends.items():
            if abs(tr.drift_pct) > 3:
                direction = "above" if tr.drift_pct > 0 else "below"
                findings.append(
                    f"- {param} trending {abs(tr.drift_pct):.1f}% {direction} baseline"
                )

        # Faults with correlated anomalies
        for fc in faults:
            if fc.correlated_anomalies:
                params = set(a.parameter for a in fc.correlated_anomalies)
                findings.append(
                    f"- {fc.fault_event} correlated with anomalies in: "
                    + ", ".join(sorted(params))
                )

        # Outlier tools
        for comp in comparisons:
            for tool in comp.outlier_tools:
                tool_mean = comp.tool_stats[tool]["mean"]
                fleet_mean = comp.fleet_baseline["mean"]
                if fleet_mean != 0:
                    pct = abs(tool_mean - fleet_mean) / abs(fleet_mean) * 100
                    direction = "above" if tool_mean > fleet_mean else "below"
                    findings.append(
                        f"- Tool {tool} performing {pct:.0f}% {direction} fleet "
                        f"average on {comp.parameter}"
                    )

        if not findings:
            return "### Key Findings\nNo significant issues detected."

        return "### Key Findings\n" + "\n".join(findings)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _unique_tools(records: list[dict]) -> set[str]:
        tools: set[str] = set()
        for rec in records:
            tid = rec.get("tool_id")
            if tid is not None:
                tools.add(str(tid))
        return tools if tools else {"unknown"}

    @staticmethod
    def _time_span(records: list[dict]) -> tuple[datetime | None, datetime | None]:
        timestamps: list[datetime] = []
        for rec in records:
            ts = rec.get("timestamp")
            if ts is None:
                continue
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            timestamps.append(ts)
        if not timestamps:
            return (None, None)
        return (min(timestamps), max(timestamps))
