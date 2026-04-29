"""Tests for envoy_drift.watcher module."""

import os
import time
import pytest
from unittest.mock import MagicMock, patch
from envoy_drift.watcher import WatchedFile, EnvFileWatcher


@pytest.fixture
def tmp_env_files(tmp_path):
    source = tmp_path / "staging.env"
    target = tmp_path / "production.env"
    source.write_text("KEY=value\n")
    target.write_text("KEY=value\n")
    return str(source), str(target)


def test_watched_file_hash_is_stable(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("A=1\n")
    wf = WatchedFile(path=str(f))
    h1 = wf.current_hash()
    h2 = wf.current_hash()
    assert h1 == h2


def test_watched_file_hash_changes_on_write(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("A=1\n")
    wf = WatchedFile(path=str(f))
    wf.update()
    f.write_text("A=2\n")
    assert wf.has_changed()


def test_watched_file_no_change_after_update(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("A=1\n")
    wf = WatchedFile(path=str(f))
    wf.update()
    assert not wf.has_changed()


def test_watched_file_missing_returns_none(tmp_path):
    wf = WatchedFile(path=str(tmp_path / "nonexistent.env"))
    assert wf.current_hash() is None


def test_watcher_no_change_does_not_trigger_callback(tmp_env_files):
    source, target = tmp_env_files
    callback = MagicMock()
    watcher = EnvFileWatcher(source, target, on_change=callback)
    changed = watcher.check_once()
    assert not changed
    callback.assert_not_called()


def test_watcher_detects_source_change(tmp_env_files):
    source, target = tmp_env_files
    callback = MagicMock()
    watcher = EnvFileWatcher(source, target, on_change=callback)
    with open(source, "w") as f:
        f.write("KEY=changed\n")
    changed = watcher.check_once()
    assert changed
    callback.assert_called_once_with(source, target)


def test_watcher_detects_target_change(tmp_env_files):
    source, target = tmp_env_files
    callback = MagicMock()
    watcher = EnvFileWatcher(source, target, on_change=callback)
    with open(target, "w") as f:
        f.write("KEY=new_value\nEXTRA=1\n")
    changed = watcher.check_once()
    assert changed
    callback.assert_called_once_with(source, target)


def test_watcher_watch_respects_max_iterations(tmp_env_files):
    source, target = tmp_env_files
    callback = MagicMock()
    watcher = EnvFileWatcher(source, target, on_change=callback, poll_interval=0.0)
    watcher.watch(max_iterations=3)
    # No changes => callback never called
    callback.assert_not_called()


def test_watcher_second_check_no_double_trigger(tmp_env_files):
    source, target = tmp_env_files
    callback = MagicMock()
    watcher = EnvFileWatcher(source, target, on_change=callback)
    with open(source, "w") as f:
        f.write("KEY=changed\n")
    watcher.check_once()
    watcher.check_once()  # second check — file not changed again
    assert callback.call_count == 1
