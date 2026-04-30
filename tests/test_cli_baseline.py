"""Tests for envoy_drift.cli_baseline module."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envoy_drift.baseline import BaselineManager
from envoy_drift.cli_baseline import build_baseline_parser, run_baseline_command


@pytest.fixture
def tmp_baseline_dir(tmp_path: Path) -> str:
    return str(tmp_path / "baselines")


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_ENV=staging\nDB_HOST=localhost\n")
    return p


def _parse(args: list[str]) -> argparse.Namespace:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_baseline_parser(sub)
    return root.parse_args(args)


def test_build_baseline_parser_registers_subcommand() -> None:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    p = build_baseline_parser(sub)
    assert p is not None


def test_save_exit_zero(env_file: Path, tmp_baseline_dir: str) -> None:
    ns = _parse(["baseline", "save", str(env_file), "v1", "--dir", tmp_baseline_dir])
    code = run_baseline_command(ns)
    assert code == 0


def test_save_creates_baseline(env_file: Path, tmp_baseline_dir: str) -> None:
    ns = _parse(["baseline", "save", str(env_file), "mybase", "--dir", tmp_baseline_dir])
    run_baseline_command(ns)
    manager = BaselineManager(tmp_baseline_dir)
    assert "mybase" in manager.list_baselines()


def test_list_no_baselines(tmp_baseline_dir: str, capsys: pytest.CaptureFixture) -> None:
    ns = _parse(["baseline", "list", "--dir", tmp_baseline_dir])
    code = run_baseline_command(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "No baselines" in out


def test_list_shows_saved(env_file: Path, tmp_baseline_dir: str, capsys: pytest.CaptureFixture) -> None:
    save_ns = _parse(["baseline", "save", str(env_file), "rel1", "--dir", tmp_baseline_dir])
    run_baseline_command(save_ns)
    list_ns = _parse(["baseline", "list", "--dir", tmp_baseline_dir])
    run_baseline_command(list_ns)
    out = capsys.readouterr().out
    assert "rel1" in out


def test_delete_existing(env_file: Path, tmp_baseline_dir: str) -> None:
    save_ns = _parse(["baseline", "save", str(env_file), "old", "--dir", tmp_baseline_dir])
    run_baseline_command(save_ns)
    del_ns = _parse(["baseline", "delete", "old", "--dir", tmp_baseline_dir])
    code = run_baseline_command(del_ns)
    assert code == 0


def test_delete_missing_returns_one(tmp_baseline_dir: str) -> None:
    ns = _parse(["baseline", "delete", "ghost", "--dir", tmp_baseline_dir])
    code = run_baseline_command(ns)
    assert code == 1


def test_compare_no_drift_exit_zero(env_file: Path, tmp_baseline_dir: str) -> None:
    save_ns = _parse(["baseline", "save", str(env_file), "base", "--dir", tmp_baseline_dir])
    run_baseline_command(save_ns)
    cmp_ns = _parse(["baseline", "compare", str(env_file), "base", "--dir", tmp_baseline_dir])
    code = run_baseline_command(cmp_ns)
    assert code == 0
