"""Snapshot support for saving and loading drift reports to/from JSON."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from envoy_drift.comparator import DriftReport


SNAPSHOT_VERSION = "1"


class SnapshotManager:
    """Serialise and deserialise DriftReport snapshots."""

    def __init__(self, snapshot_dir: str = ".envoy_snapshots") -> None:
        self.snapshot_dir = snapshot_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, report: DriftReport, label: Optional[str] = None) -> str:
        """Persist *report* to disk and return the file path."""
        os.makedirs(self.snapshot_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{label}-{timestamp}.json" if label else f"{timestamp}.json"
        path = os.path.join(self.snapshot_dir, filename)
        payload = self._serialise(report)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return path

    def load(self, path: str) -> DriftReport:
        """Load a DriftReport from a snapshot file at *path*."""
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return self._deserialise(payload)

    def list_snapshots(self) -> list[str]:
        """Return sorted list of snapshot file paths in *snapshot_dir*."""
        if not os.path.isdir(self.snapshot_dir):
            return []
        files = [
            os.path.join(self.snapshot_dir, f)
            for f in os.listdir(self.snapshot_dir)
            if f.endswith(".json")
        ]
        return sorted(files)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialise(report: DriftReport) -> dict:
        return {
            "version": SNAPSHOT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "missing_in_target": list(report.missing_in_target),
            "missing_in_source": list(report.missing_in_source),
            "value_changes": {
                k: {"source": v[0], "target": v[1]}
                for k, v in report.value_changes.items()
            },
        }

    @staticmethod
    def _deserialise(payload: dict) -> DriftReport:
        value_changes = {
            k: (v["source"], v["target"])
            for k, v in payload.get("value_changes", {}).items()
        }
        return DriftReport(
            missing_in_target=set(payload.get("missing_in_target", [])),
            missing_in_source=set(payload.get("missing_in_source", [])),
            value_changes=value_changes,
        )
