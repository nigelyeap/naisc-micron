"""
Cross-tool comparison for semiconductor equipment fleets.

Compares performance metrics across different tools/chambers by
computing summary statistics per tool and identifying outliers
relative to the fleet baseline.
"""

from __future__ import annotations

import statistics as stats
from dataclasses import dataclass


@dataclass
class ToolComparison:
    """Comparison result for a single parameter across tools."""

    parameter: str
    tool_stats: dict[str, dict]  # tool_id -> {mean, std, min, max, median, count}
    fleet_baseline: dict  # {mean, std, min, max}
    outlier_tools: list[str]  # tools that deviate significantly


class CrossToolComparator:
    """Compare performance metrics across different tools/chambers.

    No required constructor arguments.
    """

    def __init__(
        self,
        tool_id_field: str = "tool_id",
        outlier_z_threshold: float = 2.0,
    ) -> None:
        self.tool_id_field = tool_id_field
        self.outlier_z_threshold = outlier_z_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare(self, records: list[dict], parameter: str) -> ToolComparison:
        """Compare a single *parameter* across all tools in *records*."""
        groups = self._group_by_tool(records, parameter)

        tool_stats: dict[str, dict] = {}
        all_values: list[float] = []

        for tool_id, values in groups.items():
            tool_stats[tool_id] = self._summarise(values)
            all_values.extend(values)

        fleet_baseline = self._fleet_baseline(all_values)
        outlier_tools = self._find_outliers(tool_stats, fleet_baseline)

        return ToolComparison(
            parameter=parameter,
            tool_stats=tool_stats,
            fleet_baseline=fleet_baseline,
            outlier_tools=outlier_tools,
        )

    def compare_all(self, records: list[dict]) -> list[ToolComparison]:
        """Compare every numeric parameter found in *records*."""
        if not records:
            return []
        parameters = self._infer_parameters(records)
        return [self.compare(records, p) for p in parameters]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _group_by_tool(
        self,
        records: list[dict],
        parameter: str,
    ) -> dict[str, list[float]]:
        groups: dict[str, list[float]] = {}
        for rec in records:
            tool_id = rec.get(self.tool_id_field)
            val = rec.get(parameter)
            if tool_id is None or val is None:
                continue
            if not isinstance(val, (int, float)):
                continue
            groups.setdefault(str(tool_id), []).append(float(val))
        return groups

    @staticmethod
    def _summarise(values: list[float]) -> dict:
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0, "count": 0}
        mean = stats.mean(values)
        std = stats.pstdev(values) if len(values) > 1 else 0.0
        return {
            "mean": round(mean, 6),
            "std": round(std, 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "median": round(stats.median(values), 6),
            "count": len(values),
        }

    @staticmethod
    def _fleet_baseline(all_values: list[float]) -> dict:
        if not all_values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}
        mean = stats.mean(all_values)
        std = stats.pstdev(all_values) if len(all_values) > 1 else 0.0
        return {
            "mean": round(mean, 6),
            "std": round(std, 6),
            "min": round(min(all_values), 6),
            "max": round(max(all_values), 6),
        }

    def _find_outliers(
        self,
        tool_stats: dict[str, dict],
        fleet_baseline: dict,
    ) -> list[str]:
        """A tool is an outlier if its mean is more than
        ``outlier_z_threshold`` fleet standard deviations from the
        fleet mean."""
        fleet_std = fleet_baseline.get("std", 0)
        fleet_mean = fleet_baseline.get("mean", 0)
        if fleet_std == 0:
            return []

        outliers: list[str] = []
        for tool_id, st in tool_stats.items():
            z = abs(st["mean"] - fleet_mean) / fleet_std
            if z >= self.outlier_z_threshold:
                outliers.append(tool_id)
        return sorted(outliers)

    @staticmethod
    def _infer_parameters(records: list[dict]) -> list[str]:
        skip = {"timestamp", "record_id", "tool_id", "alarm", "fault", "event"}
        return [
            k
            for k, v in records[0].items()
            if k.lower() not in skip and isinstance(v, (int, float))
        ]
