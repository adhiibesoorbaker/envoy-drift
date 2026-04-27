"""Filtering utilities for drift reports — allows ignoring keys by pattern."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class DriftFilter:
    """Holds a collection of glob/regex patterns used to exclude env keys from drift analysis."""

    patterns: list[str] = field(default_factory=list)
    use_regex: bool = False

    def add_pattern(self, pattern: str) -> None:
        """Register a new exclusion pattern."""
        self.patterns.append(pattern)

    def should_exclude(self, key: str) -> bool:
        """Return True if *key* matches any registered exclusion pattern."""
        for pattern in self.patterns:
            if self.use_regex:
                if re.fullmatch(pattern, key):
                    return True
            else:
                if fnmatch.fnmatch(key, pattern):
                    return True
        return False

    def filter_keys(self, keys: Iterable[str]) -> list[str]:
        """Return only the keys that are *not* excluded."""
        return [k for k in keys if not self.should_exclude(k)]

    def apply_to_env(self, env: dict[str, str]) -> dict[str, str]:
        """Return a copy of *env* with excluded keys removed."""
        return {k: v for k, v in env.items() if not self.should_exclude(k)}


def build_filter(
    patterns: Iterable[str] | None = None,
    use_regex: bool = False,
) -> DriftFilter:
    """Convenience factory that creates a :class:`DriftFilter` from an iterable of patterns."""
    drift_filter = DriftFilter(use_regex=use_regex)
    for pattern in patterns or []:
        drift_filter.add_pattern(pattern)
    return drift_filter
