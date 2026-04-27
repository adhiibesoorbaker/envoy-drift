"""Tests for the CLI entry point."""

import textwrap
from pathlib import Path

import pytest

from envoy_drift.cli import run


@pytest.fixture
def env_staging(tmp_path: Path) -> Path:
    p = tmp_path / ".env.staging"
    p.write_text(textwrap.dedent("""\
        APP_ENV=staging
        DB_HOST=staging-db.internal
        LOG_LEVEL=debug
        SECRET_KEY=abc123
    """))
    return p


@pytest.fixture
def env_production(tmp_path: Path) -> Path:
    p = tmp_path / ".env.production"
    p.write_text(textwrap.dedent("""\
        APP_ENV=production
        DB_HOST=prod-db.internal
        LOG_LEVEL=info
        SECRET_KEY=abc123
    """))
    return p


@pytest.fixture
def env_identical(tmp_path: Path) -> Path:
    p = tmp_path / ".env.identical"
    p.write_text(textwrap.dedent("""\
        APP_ENV=staging
        DB_HOST=staging-db.internal
        LOG_LEVEL=debug
        SECRET_KEY=abc123
    """))
    return p


def test_exit_code_zero_no_drift(env_staging, env_identical):
    code = run([str(env_staging), str(env_identical), "--exit-code"])
    assert code == 0


def test_exit_code_one_with_drift(env_staging, env_production):
    code = run([str(env_staging), str(env_production), "--exit-code"])
    assert code == 1


def test_exit_code_zero_without_flag_even_with_drift(env_staging, env_production):
    code = run([str(env_staging), str(env_production)])
    assert code == 0


def test_missing_source_returns_2(tmp_path, env_production):
    code = run([str(tmp_path / "nonexistent.env"), str(env_production)])
    assert code == 2


def test_missing_target_returns_2(tmp_path, env_staging):
    code = run([str(env_staging), str(tmp_path / "nonexistent.env")])
    assert code == 2


def test_json_format_runs_without_error(env_staging, env_production, capsys):
    code = run([str(env_staging), str(env_production), "--format", "json"])
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert "has_drift" in data


def test_markdown_format_runs_without_error(env_staging, env_production, capsys):
    code = run([str(env_staging), str(env_production), "--format", "markdown"])
    captured = capsys.readouterr()
    assert "## Drift Report" in captured.out
