"""Tests for the EnvComparator and DriftReport classes."""

import pytest
from envoy_drift.comparator import DriftReport, EnvComparator


@pytest.fixture
def comparator():
    return EnvComparator()


def test_no_drift_identical_envs(comparator):
    source = {"APP_ENV": "staging", "DB_HOST": "localhost", "PORT": "8080"}
    target = {"APP_ENV": "staging", "DB_HOST": "localhost", "PORT": "8080"}
    report = comparator.compare(source, target)
    assert not report.has_drift


def test_no_drift_empty_envs(comparator):
    report = comparator.compare({}, {})
    assert not report.has_drift


def test_detects_key_missing_in_target(comparator):
    source = {"APP_ENV": "staging", "SECRET_KEY": "abc123"}
    target = {"APP_ENV": "staging"}
    report = comparator.compare(source, target)
    assert report.has_drift
    assert "SECRET_KEY" in report.missing_in_target
    assert report.missing_in_target["SECRET_KEY"] == "abc123"
    assert not report.missing_in_source
    assert not report.value_differences


def test_detects_key_missing_in_source(comparator):
    source = {"APP_ENV": "production"}
    target = {"APP_ENV": "production", "NEW_FEATURE_FLAG": "true"}
    report = comparator.compare(source, target)
    assert report.has_drift
    assert "NEW_FEATURE_FLAG" in report.missing_in_source
    assert report.missing_in_source["NEW_FEATURE_FLAG"] == "true"
    assert not report.missing_in_target
    assert not report.value_differences


def test_detects_value_difference(comparator):
    source = {"DB_HOST": "staging-db.internal", "PORT": "5432"}
    target = {"DB_HOST": "prod-db.internal", "PORT": "5432"}
    report = comparator.compare(source, target)
    assert report.has_drift
    assert "DB_HOST" in report.value_differences
    assert report.value_differences["DB_HOST"] == ("staging-db.internal", "prod-db.internal")
    assert "PORT" not in report.value_differences


def test_detects_multiple_drift_types(comparator):
    source = {"APP_ENV": "staging", "OLD_KEY": "old", "SHARED": "v1"}
    target = {"APP_ENV": "staging", "NEW_KEY": "new", "SHARED": "v2"}
    report = comparator.compare(source, target)
    assert report.has_drift
    assert "OLD_KEY" in report.missing_in_target
    assert "NEW_KEY" in report.missing_in_source
    assert "SHARED" in report.value_differences


def test_summary_no_drift(comparator):
    report = comparator.compare({"KEY": "val"}, {"KEY": "val"})
    assert "No drift detected" in report.summary()


def test_summary_with_drift(comparator):
    source = {"ONLY_SOURCE": "s", "COMMON": "old"}
    target = {"ONLY_TARGET": "t", "COMMON": "new"}
    report = comparator.compare(source, target)
    summary = report.summary()
    assert "Drift detected" in summary
    assert "ONLY_SOURCE" in summary
    assert "ONLY_TARGET" in summary
    assert "COMMON" in summary
    assert "old" in summary
    assert "new" in summary


def test_drift_report_defaults():
    report = DriftReport()
    assert report.missing_in_target == {}
    assert report.missing_in_source == {}
    assert report.value_differences == {}
    assert not report.has_drift
