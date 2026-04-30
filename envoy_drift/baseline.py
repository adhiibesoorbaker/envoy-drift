"""Baseline management for envoy-drift.

Allows saving a known-good env configuration as a baseline and
comparing future states against it to detect drift over time.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_BASELINE_DIR = ".envoy_baselines"


class BaselineManager:
    """Manages saving and loading of env baselines."""

    def __init__(self, baseline_dir: str = DEFAULT_BASELINE_DIR) -> None:
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def save(self, env: dict[str, str], name: str) -> Path:
        """Save an env dict as a named baseline."""
        record = {
            "name": name,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "env": env,
        }
        path = self.baseline_dir / f"{name}.json"
        path.write_text(json.dumps(record, indent=2))
        return path

    def load(self, name: str) -> dict[str, str]:
        """Load a named baseline and return its env dict."""
        path = self.baseline_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Baseline '{name}' not found at {path}")
        record = json.loads(path.read_text())
        return record["env"]

    def list_baselines(self) -> list[str]:
        """Return sorted list of saved baseline names."""
        return sorted(
            p.stem for p in self.baseline_dir.glob("*.json")
        )

    def delete(self, name: str) -> bool:
        """Delete a baseline by name. Returns True if deleted."""
        path = self.baseline_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def metadata(self, name: str) -> dict:
        """Return full metadata record for a baseline."""
        path = self.baseline_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Baseline '{name}' not found at {path}")
        return json.loads(path.read_text())
