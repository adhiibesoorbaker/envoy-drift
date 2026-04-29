"""Export drift reports to various file formats (JSON, CSV)."""

import csv
import json
import io
from enum import Enum
from typing import IO

from envoy_drift.comparator import DriftReport


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"


class DriftExporter:
    """Exports a DriftReport to JSON or CSV format."""

    def __init__(self, report: DriftReport):
        self.report = report

    def export(self, fmt: ExportFormat) -> str:
        """Return the report serialised as a string in the given format."""
        if fmt == ExportFormat.JSON:
            return self._to_json()
        if fmt == ExportFormat.CSV:
            return self._to_csv()
        raise ValueError(f"Unsupported export format: {fmt}")

    def write(self, fmt: ExportFormat, stream: IO[str]) -> None:
        """Write the serialised report to an open text stream."""
        stream.write(self.export(fmt))

    def _to_json(self) -> str:
        payload = {
            "has_drift": self.report.has_drift,
            "missing_in_target": list(self.report.missing_in_target),
            "missing_in_source": list(self.report.missing_in_source),
            "changed_values": {
                k: {"source": v[0], "target": v[1]}
                for k, v in self.report.changed_values.items()
            },
        }
        return json.dumps(payload, indent=2)

    def _to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["key", "status", "source_value", "target_value"])

        for key in sorted(self.report.missing_in_target):
            writer.writerow([key, "missing_in_target", "", ""])

        for key in sorted(self.report.missing_in_source):
            writer.writerow([key, "missing_in_source", "", ""])

        for key, (src, tgt) in sorted(self.report.changed_values.items()):
            writer.writerow([key, "changed", src, tgt])

        return buf.getvalue()
