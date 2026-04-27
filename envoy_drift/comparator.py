"""Core comparison logic for detecting drift between two env dictionaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envoy_drift.filters import DriftFilter


@dataclass
class DriftReport:
    """Holds the results of comparing a source and target env mapping."""

    missing_in_target: list[str] = field(default_factory=list)
    missing_in_source: list[str] = field(default_factory=list)
    value_differences: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        """Return True when any drift was detected."""
        return bool(
            self.missing_in_target
            or self.missing_in_source
            or self.value_differences
        )

    def summary(self) -> str:
        """Return a short human-readable summary line."""
        if not self.has_drift:
            return "No drift detected."
        parts: list[str] = []
        if self.missing_in_target:
            parts.append(f"{len(self.missing_in_target)} key(s) missing in target")
        if self.missing_in_source:
            parts.append(f"{len(self.missing_in_source)} key(s) missing in source")
        if self.value_differences:
            parts.append(f"{len(self.value_differences)} value difference(s)")
        return "Drift detected: " + ", ".join(parts) + "."


class EnvComparator:
    """Compares two env dictionaries and produces a :class:`DriftReport`."""

    def __init__(self, drift_filter: "DriftFilter | None" = None) -> None:
        self._filter = drift_filter

    def compare(
        self,
        source: dict[str, str],
        target: dict[str, str],
    ) -> DriftReport:
        """Compare *source* against *target*, respecting any configured filter."""
        if self._filter is not None:
            source = self._filter.apply_to_env(source)
            target = self._filter.apply_to_env(target)

        source_keys = set(source)
        target_keys = set(target)

        missing_in_target = sorted(source_keys - target_keys)
        missing_in_source = sorted(target_keys - source_keys)

        value_differences: dict[str, tuple[str, str]] = {}
        for key in source_keys & target_keys:
            if source[key] != target[key]:
                value_differences[key] = (source[key], target[key])

        return DriftReport(
            missing_in_target=missing_in_target,
            missing_in_source=missing_in_source,
            value_differences=value_differences,
        )
