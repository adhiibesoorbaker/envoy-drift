"""Tests for the snapshot CLI subcommand (cli_snapshot.py)."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from envoy_drift.cli_snapshot import build_snapshot_parser, run_snapshot_command
from envoy_drift.snapshot import SnapshotManager
from envoy_drift.comparator import DriftReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_snapshot_dir(tmp_path: Path) -> Path:
    """Return a temporary directory to store snapshots."""
    d = tmp_path / "snapshots"
    d.mkdir()
    return d


@pytest.fixture()
def sample_report() -> DriftReport:
    """Return a minimal DriftReport with some drift."""
    return DriftReport(
        missing_in_target={"DB_PASSWORD"},
        missing_in_source=set(),
        value_diffs={"API_URL": ("http://staging.example.com", "http://prod.example.com")},
    )


@pytest.fixture()
def saved_snapshot(tmp_snapshot_dir: Path, sample_report: DriftReport) -> str:
    """Pre-save a snapshot and return its filename stem."""
    manager = SnapshotManager(snapshot_dir=str(tmp_snapshot_dir))
    filename = manager.save(sample_report, label="pre-test")
    return filename


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_build_snapshot_parser_returns_parser():
    parser = build_snapshot_parser()
    assert parser is not None


def test_snapshot_parser_has_subcommands():
    parser = build_snapshot_parser()
    # Should not raise when parsing known subcommands
    args = parser.parse_args(["list"])
    assert args.snapshot_cmd == "list"


def test_snapshot_parser_show_requires_name():
    parser = build_snapshot_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["show"])  # missing required <name> argument


def test_snapshot_parser_show_accepts_name():
    parser = build_snapshot_parser()
    args = parser.parse_args(["show", "my-snapshot.json"])
    assert args.snapshot_cmd == "show"
    assert args.name == "my-snapshot.json"


# ---------------------------------------------------------------------------
# run_snapshot_command — list
# ---------------------------------------------------------------------------

def test_list_no_snapshots(tmp_snapshot_dir: Path, capsys):
    parser = build_snapshot_parser()
    args = parser.parse_args(["list"])
    args.snapshot_dir = str(tmp_snapshot_dir)

    exit_code = run_snapshot_command(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "no snapshots" in captured.out.lower() or captured.out.strip() == ""


def test_list_shows_saved_snapshot(tmp_snapshot_dir: Path, saved_snapshot: str, capsys):
    parser = build_snapshot_parser()
    args = parser.parse_args(["list"])
    args.snapshot_dir = str(tmp_snapshot_dir)

    exit_code = run_snapshot_command(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    # The saved filename should appear in the listing
    assert saved_snapshot in captured.out


# ---------------------------------------------------------------------------
# run_snapshot_command — show
# ---------------------------------------------------------------------------

def test_show_existing_snapshot(tmp_snapshot_dir: Path, saved_snapshot: str, capsys):
    parser = build_snapshot_parser()
    args = parser.parse_args(["show", saved_snapshot])
    args.snapshot_dir = str(tmp_snapshot_dir)

    exit_code = run_snapshot_command(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    # Drift details should be rendered
    assert "DB_PASSWORD" in captured.out or "API_URL" in captured.out


def test_show_missing_snapshot_returns_nonzero(tmp_snapshot_dir: Path, capsys):
    parser = build_snapshot_parser()
    args = parser.parse_args(["show", "nonexistent-snapshot.json"])
    args.snapshot_dir = str(tmp_snapshot_dir)

    exit_code = run_snapshot_command(args)

    assert exit_code != 0


def test_show_missing_snapshot_prints_error(tmp_snapshot_dir: Path, capsys):
    parser = build_snapshot_parser()
    args = parser.parse_args(["show", "ghost.json"])
    args.snapshot_dir = str(tmp_snapshot_dir)

    run_snapshot_command(args)

    captured = capsys.readouterr()
    assert "not found" in captured.err.lower() or "error" in captured.err.lower() or "ghost.json" in captured.out
