"""Tests for envoy_drift.baseline module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envoy_drift.baseline import BaselineManager


@pytest.fixture
def tmp_baseline_dir(tmp_path: Path) -> Path:
    return tmp_path / "baselines"


@pytest.fixture
def manager(tmp_baseline_dir: Path) -> BaselineManager:
    return BaselineManager(baseline_dir=str(tmp_baseline_dir))


SAMPLE_ENV = {"APP_ENV": "staging", "DB_HOST": "localhost", "PORT": "5432"}


def test_save_creates_file(manager: BaselineManager, tmp_baseline_dir: Path) -> None:
    path = manager.save(SAMPLE_ENV, "v1")
    assert path.exists()
    assert path.name == "v1.json"


def test_save_stores_env(manager: BaselineManager) -> None:
    manager.save(SAMPLE_ENV, "v1")
    loaded = manager.load("v1")
    assert loaded == SAMPLE_ENV


def test_save_includes_metadata(manager: BaselineManager, tmp_baseline_dir: Path) -> None:
    manager.save(SAMPLE_ENV, "v1")
    raw = json.loads((tmp_baseline_dir / "v1.json").read_text())
    assert raw["name"] == "v1"
    assert "saved_at" in raw


def test_load_missing_raises(manager: BaselineManager) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        manager.load("ghost")


def test_list_empty(manager: BaselineManager) -> None:
    assert manager.list_baselines() == []


def test_list_returns_names(manager: BaselineManager) -> None:
    manager.save(SAMPLE_ENV, "alpha")
    manager.save(SAMPLE_ENV, "beta")
    assert manager.list_baselines() == ["alpha", "beta"]


def test_delete_existing(manager: BaselineManager) -> None:
    manager.save(SAMPLE_ENV, "v1")
    result = manager.delete("v1")
    assert result is True
    assert manager.list_baselines() == []


def test_delete_nonexistent(manager: BaselineManager) -> None:
    result = manager.delete("nope")
    assert result is False


def test_metadata_returns_full_record(manager: BaselineManager) -> None:
    manager.save(SAMPLE_ENV, "v1")
    meta = manager.metadata("v1")
    assert meta["name"] == "v1"
    assert meta["env"] == SAMPLE_ENV
    assert "saved_at" in meta


def test_metadata_missing_raises(manager: BaselineManager) -> None:
    with pytest.raises(FileNotFoundError):
        manager.metadata("missing")
