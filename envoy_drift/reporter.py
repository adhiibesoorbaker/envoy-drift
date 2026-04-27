"""Formats and outputs drift reports in various formats."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from envoy_drift.comparator import DriftReport


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


class DriftReporter:
    """Renders a DriftReport to a chosen output format."""

    def __init__(self, fmt: OutputFormat = OutputFormat.TEXT, stream: TextIO = sys.stdout):
        self.fmt = fmt
        self.stream = stream

    def render(self, report: DriftReport) -> None:
        if self.fmt == OutputFormat.TEXT:
            self._render_text(report)
        elif self.fmt == OutputFormat.JSON:
            self._render_json(report)
        elif self.fmt == OutputFormat.MARKDOWN:
            self._render_markdown(report)

    def _render_text(self, report: DriftReport) -> None:
        if not report.has_drift:
            self.stream.write("✓ No drift detected.\n")
            return
        self.stream.write(f"⚠ Drift detected: {report.summary}\n")
        if report.missing_in_target:
            self.stream.write("\nMissing in target:\n")
            for key in sorted(report.missing_in_target):
                self.stream.write(f"  - {key}\n")
        if report.missing_in_source:
            self.stream.write("\nMissing in source:\n")
            for key in sorted(report.missing_in_source):
                self.stream.write(f"  + {key}\n")
        if report.value_mismatches:
            self.stream.write("\nValue mismatches:\n")
            for key, (src, tgt) in sorted(report.value_mismatches.items()):
                self.stream.write(f"  ~ {key}: {src!r} → {tgt!r}\n")

    def _render_json(self, report: DriftReport) -> None:
        import json
        data = {
            "has_drift": report.has_drift,
            "summary": report.summary,
            "missing_in_target": sorted(report.missing_in_target),
            "missing_in_source": sorted(report.missing_in_source),
            "value_mismatches": {
                k: {"source": v[0], "target": v[1]}
                for k, v in sorted(report.value_mismatches.items())
            },
        }
        self.stream.write(json.dumps(data, indent=2) + "\n")

    def _render_markdown(self, report: DriftReport) -> None:
        self.stream.write("## Drift Report\n\n")
        if not report.has_drift:
            self.stream.write("✅ No drift detected.\n")
            return
        self.stream.write(f"**{report.summary}**\n")
        if report.missing_in_target:
            self.stream.write("\n### Missing in target\n")
            for key in sorted(report.missing_in_target):
                self.stream.write(f"- `{key}`\n")
        if report.missing_in_source:
            self.stream.write("\n### Missing in source\n")
            for key in sorted(report.missing_in_source):
                self.stream.write(f"- `{key}`\n")
        if report.value_mismatches:
            self.stream.write("\n### Value mismatches\n")
            self.stream.write("| Key | Source | Target |\n")
            self.stream.write("|-----|--------|--------|\n")
            for key, (src, tgt) in sorted(report.value_mismatches.items()):
                self.stream.write(f"| `{key}` | `{src}` | `{tgt}` |\n")
