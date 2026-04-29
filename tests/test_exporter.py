"""Tests for envoy_drift.exporter."""

import csv
import io
import json

import pytest

from envoy_drift.comparator import DriftReport
from envoy_drift.exporter import DriftExporter, ExportFormat


@pytest.fixture()
def no_drift_report():
    return DriftReport(
        missing_in_target=set(),
        missing_in_source=set(),
        changed_values={},
    )


@pytest.fixture()
def drift_report():
    return DriftReport(
        missing_in_target={"ONLY_IN_SOURCE"},
        missing_in_source={"ONLY_IN_TARGET"},
        changed_values={"DB_HOST": ("localhost", "prod.db.internal")},
    )


# --- JSON export ---

def test_json_no_drift(no_drift_report):
    exporter = DriftExporter(no_drift_report)
    result = json.loads(exporter.export(ExportFormat.JSON))
    assert result["has_drift"] is False
    assert result["missing_in_target"] == []
    assert result["missing_in_source"] == []
    assert result["changed_values"] == {}


def test_json_with_drift(drift_report):
    exporter = DriftExporter(drift_report)
    result = json.loads(exporter.export(ExportFormat.JSON))
    assert result["has_drift"] is True
    assert "ONLY_IN_SOURCE" in result["missing_in_target"]
    assert "ONLY_IN_TARGET" in result["missing_in_source"]
    assert result["changed_values"]["DB_HOST"] == {
        "source": "localhost",
        "target": "prod.db.internal",
    }


# --- CSV export ---

def test_csv_headers(no_drift_report):
    exporter = DriftExporter(no_drift_report)
    lines = exporter.export(ExportFormat.CSV).splitlines()
    assert lines[0] == "key,status,source_value,target_value"


def test_csv_with_drift(drift_report):
    exporter = DriftExporter(drift_report)
    raw = exporter.export(ExportFormat.CSV)
    reader = csv.DictReader(io.StringIO(raw))
    rows = {row["key"]: row for row in reader}

    assert rows["ONLY_IN_SOURCE"]["status"] == "missing_in_target"
    assert rows["ONLY_IN_TARGET"]["status"] == "missing_in_source"
    assert rows["DB_HOST"]["status"] == "changed"
    assert rows["DB_HOST"]["source_value"] == "localhost"
    assert rows["DB_HOST"]["target_value"] == "prod.db.internal"


# --- write helper ---

def test_write_outputs_to_stream(drift_report):
    exporter = DriftExporter(drift_report)
    buf = io.StringIO()
    exporter.write(ExportFormat.JSON, buf)
    buf.seek(0)
    result = json.loads(buf.read())
    assert result["has_drift"] is True


def test_unsupported_format_raises(no_drift_report):
    exporter = DriftExporter(no_drift_report)
    with pytest.raises(ValueError, match="Unsupported export format"):
        exporter.export("xml")  # type: ignore[arg-type]
