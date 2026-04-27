"""Comparator module for detecting drift between two environment configurations."""

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class DriftReport:
    """Holds the result of comparing two environment configurations."""

    missing_in_target: Dict[str, str] = field(default_factory=dict)
    missing_in_source: Dict[str, str] = field(default_factory=dict)
    value_differences: Dict[str, tuple] = field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        """Return True if any drift was detected."""
        return bool(
            self.missing_in_target
            or self.missing_in_source
            or self.value_differences
        )

    def summary(self) -> str:
        """Return a human-readable summary of the drift report."""
        if not self.has_drift:
            return "No drift detected. Environments are in sync."

        lines = ["Drift detected:\n"]

        if self.missing_in_target:
            lines.append("  Keys missing in target:")
            for key in sorted(self.missing_in_target):
                lines.append(f"    - {key}={self.missing_in_target[key]}")

        if self.missing_in_source:
            lines.append("  Keys missing in source:")
            for key in sorted(self.missing_in_source):
                lines.append(f"    + {key}={self.missing_in_source[key]}")

        if self.value_differences:
            lines.append("  Value differences:")
            for key in sorted(self.value_differences):
                source_val, target_val = self.value_differences[key]
                lines.append(f"    ~ {key}: '{source_val}' -> '{target_val}'")

        return "\n".join(lines)


class EnvComparator:
    """Compares two environment variable dictionaries and produces a DriftReport."""

    def compare(
        self,
        source: Dict[str, str],
        target: Dict[str, str],
    ) -> DriftReport:
        """Compare source env against target env and return a DriftReport.

        Args:
            source: The baseline environment (e.g. staging).
            target: The environment to compare against (e.g. production).

        Returns:
            A DriftReport describing all detected differences.
        """
        report = DriftReport()

        source_keys: Set[str] = set(source.keys())
        target_keys: Set[str] = set(target.keys())

        for key in source_keys - target_keys:
            report.missing_in_target[key] = source[key]

        for key in target_keys - source_keys:
            report.missing_in_source[key] = target[key]

        for key in source_keys & target_keys:
            if source[key] != target[key]:
                report.value_differences[key] = (source[key], target[key])

        return report
