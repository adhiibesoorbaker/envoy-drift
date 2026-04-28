"""Line-level diff utilities for env file values."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ValueDiff:
    """Represents a value-level difference for a single key."""

    key: str
    source_value: Optional[str]
    target_value: Optional[str]

    @property
    def is_missing_in_source(self) -> bool:
        return self.source_value is None

    @property
    def is_missing_in_target(self) -> bool:
        return self.target_value is None

    @property
    def is_changed(self) -> bool:
        return (
            self.source_value is not None
            and self.target_value is not None
            and self.source_value != self.target_value
        )

    def describe(self) -> str:
        if self.is_missing_in_source:
            return f"{self.key}: missing in source (target={self.target_value!r})"
        if self.is_missing_in_target:
            return f"{self.key}: missing in target (source={self.source_value!r})"
        if self.is_changed:
            return f"{self.key}: {self.source_value!r} -> {self.target_value!r}"
        return f"{self.key}: unchanged"


@dataclass
class EnvDiff:
    """Full diff between two env dictionaries."""

    diffs: List[ValueDiff] = field(default_factory=list)

    @property
    def changed_keys(self) -> List[str]:
        return [d.key for d in self.diffs if d.is_changed]

    @property
    def missing_in_source(self) -> List[str]:
        return [d.key for d in self.diffs if d.is_missing_in_source]

    @property
    def missing_in_target(self) -> List[str]:
        return [d.key for d in self.diffs if d.is_missing_in_target]

    @property
    def has_differences(self) -> bool:
        return bool(self.diffs)

    def summary_lines(self) -> List[str]:
        return [d.describe() for d in self.diffs]


class EnvDiffer:
    """Computes a detailed diff between two env variable dictionaries."""

    def diff(
        self,
        source: Dict[str, str],
        target: Dict[str, str],
    ) -> EnvDiff:
        """Return an EnvDiff describing all differences between source and target."""
        all_keys = sorted(set(source) | set(target))
        diffs: List[ValueDiff] = []

        for key in all_keys:
            src_val = source.get(key)
            tgt_val = target.get(key)
            if src_val != tgt_val:
                diffs.append(ValueDiff(key=key, source_value=src_val, target_value=tgt_val))

        return EnvDiff(diffs=diffs)
