"""Tests for envoy_drift.snapshot."""

from __future__ import annotations

import json
import os

import pytest

from envoy_drift.comparator import DriftReport
from envoy_drift.snapshot import SnapshotManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_snapshot_dir(tmp_path):
    return str(tmp_path / "snapshots")


@pytest.fixture()
def manager(tmp_snapshot_dir):
    return SnapshotManager(snapshot_dir=tmp_snapshot_dir)


@pytest.fixture()
def sample_report():
    return DriftReport(
        missing_in_target={"DB_HOST"},
        missing_in_source={"NEW_RELIC_KEY"},
        value_changes={"LOG_LEVEL": ("debug", "info")},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_save_creates_file(manager, sample_report, tmp_snapshot_dir):
    path = manager.save(sample_report)
    assert os.path.isfile(path)
    assert path.startswith(tmp_snapshot_dir)


def test_save_with_label_includes_label(manager, sample_report):
    path = manager.save(sample_report, label="prod")
    assert os.path.basename(path).startswith("prod-")


def test_save_produces_valid_json(manager, sample_report):
    path = manager.save(sample_report)
    with open(path) as fh:
        data = json.load(fh)
    assert data["version"] == "1"
    assert "missing_in_target" in data
    assert "missing_in_source" in data
    assert "value_changes" in data


def test_roundtrip_preserves_report(manager, sample_report):
    path = manager.save(sample_report)
    loaded = manager.load(path)
    assert loaded.missing_in_target == sample_report.missing_in_target
    assert loaded.missing_in_source == sample_report.missing_in_source
    assert loaded.value_changes == sample_report.value_changes


def test_roundtrip_no_drift(manager):
    empty = DriftReport(missing_in_target=set(), missing_in_source=set(), value_changes={})
    path = manager.save(empty)
    loaded = manager.load(path)
    assert not loaded.has_drift


def test_list_snapshots_empty_dir(manager, tmp_snapshot_dir):
    result = manager.list_snapshots()
    assert result == []


def test_list_snapshots_nonexistent_dir():
    mgr = SnapshotManager(snapshot_dir="/tmp/__nonexistent_envoy_test__")
    assert mgr.list_snapshots() == []


def test_list_snapshots_returns_sorted(manager, sample_report):
    p1 = manager.save(sample_report, label="a")
    p2 = manager.save(sample_report, label="b")
    snapshots = manager.list_snapshots()
    assert len(snapshots) == 2
    assert snapshots == sorted([p1, p2])
