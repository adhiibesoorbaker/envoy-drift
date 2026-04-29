"""Tests for envoy_drift.cli_watch module."""

import argparse
import pytest
from unittest.mock import MagicMock, patch

from envoy_drift.cli_watch import build_watch_parser, run_watch_command, _on_change_handler


@pytest.fixture
def tmp_env_files(tmp_path):
    source = tmp_path / "staging.env"
    target = tmp_path / "production.env"
    source.write_text("KEY=staging\nONLY_STAGING=1\n")
    target.write_text("KEY=production\n")
    return str(source), str(target)


def test_build_watch_parser_returns_parser():
    parser = build_watch_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_watch_parser_has_source_and_target():
    parser = build_watch_parser()
    args = parser.parse_args(["staging.env", "production.env"])
    assert args.source == "staging.env"
    assert args.target == "production.env"


def test_watch_parser_default_interval():
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env"])
    assert args.interval == 2.0


def test_watch_parser_custom_interval():
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env", "--interval", "5.0"])
    assert args.interval == 5.0


def test_watch_parser_default_format():
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env"])
    assert args.output_format == "text"


def test_watch_parser_json_format():
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env", "--format", "json"])
    assert args.output_format == "json"


def test_on_change_handler_calls_render(tmp_env_files, capsys):
    source, target = tmp_env_files
    handler = _on_change_handler("text")
    handler(source, target)
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_run_watch_command_calls_watcher(tmp_env_files):
    source, target = tmp_env_files
    args = argparse.Namespace(
        source=source,
        target=target,
        interval=0.01,
        output_format="text",
    )
    with patch("envoy_drift.cli_watch.EnvFileWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        instance.watch.side_effect = KeyboardInterrupt
        run_watch_command(args)
        MockWatcher.assert_called_once()
        instance.watch.assert_called_once()


def test_run_watch_command_prints_startup_message(tmp_env_files, capsys):
    source, target = tmp_env_files
    args = argparse.Namespace(
        source=source,
        target=target,
        interval=1.0,
        output_format="text",
    )
    with patch("envoy_drift.cli_watch.EnvFileWatcher") as MockWatcher:
        MockWatcher.return_value.watch.side_effect = KeyboardInterrupt
        run_watch_command(args)
    captured = capsys.readouterr()
    assert "Watching" in captured.out
