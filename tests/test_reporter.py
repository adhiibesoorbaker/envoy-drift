"""Tests for the DriftReporter module."""

import io
import json
import pytest

from envoy_drift.comparator import DriftReport
from envoy_drift.reporter import DriftReporter, OutputFormat


@pytest.fixture
def no_drift_report():
    return DriftReport(
        missing_in_target=set(),
        missing_in_source=set(),
        value_mismatches={},
    )


@pytest.fixture
def drift_report():
    return DriftReport(
        missing_in_target={"DB_HOST"},
        missing_in_source={"NEW_RELIC_KEY"},
        value_mismatches={"LOG_LEVEL": ("debug", "info")},
    )


def _capture(reporter: DriftReporter, report: DriftReport) -> str:
    reporter.render(report)
    return reporter.stream.getvalue()


def make_reporter(fmt: OutputFormat) -> DriftReporter:
    return DriftReporter(fmt=fmt, stream=io.StringIO())


# --- TEXT format ---

def test_text_no_drift(no_drift_report):
    out = _capture(make_reporter(OutputFormat.TEXT), no_drift_report)
    assert "No drift detected" in out


def test_text_shows_missing_in_target(drift_report):
    out = _capture(make_reporter(OutputFormat.TEXT), drift_report)
    assert "DB_HOST" in out
    assert "Missing in target" in out


def test_text_shows_missing_in_source(drift_report):
    out = _capture(make_reporter(OutputFormat.TEXT), drift_report)
    assert "NEW_RELIC_KEY" in out
    assert "Missing in source" in out


def test_text_shows_value_mismatch(drift_report):
    out = _capture(make_reporter(OutputFormat.TEXT), drift_report)
    assert "LOG_LEVEL" in out
    assert "debug" in out
    assert "info" in out


# --- JSON format ---

def test_json_no_drift(no_drift_report):
    out = _capture(make_reporter(OutputFormat.JSON), no_drift_report)
    data = json.loads(out)
    assert data["has_drift"] is False
    assert data["missing_in_target"] == []


def test_json_drift_structure(drift_report):
    out = _capture(make_reporter(OutputFormat.JSON), drift_report)
    data = json.loads(out)
    assert data["has_drift"] is True
    assert "DB_HOST" in data["missing_in_target"]
    assert "NEW_RELIC_KEY" in data["missing_in_source"]
    assert data["value_mismatches"]["LOG_LEVEL"] == {"source": "debug", "target": "info"}


# --- Markdown format ---

def test_markdown_no_drift(no_drift_report):
    out = _capture(make_reporter(OutputFormat.MARKDOWN), no_drift_report)
    assert "## Drift Report" in out
    assert "No drift detected" in out


def test_markdown_has_table_for_mismatches(drift_report):
    out = _capture(make_reporter(OutputFormat.MARKDOWN), drift_report)
    assert "| Key |" in out
    assert "LOG_LEVEL" in out


def test_markdown_lists_missing_keys(drift_report):
    out = _capture(make_reporter(OutputFormat.MARKDOWN), drift_report)
    assert "`DB_HOST`" in out
    assert "`NEW_RELIC_KEY`" in out
