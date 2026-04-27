"""Tests for the env file parser module."""

import os
import tempfile
import pytest

from envoy_drift.parser import EnvFileParser, load_env_file


@pytest.fixture
def tmp_env_file():
    """Create a temporary env file for testing."""
    content = """# Sample env file
APP_ENV=staging
DATABASE_URL=postgres://localhost:5432/mydb
SECRET_KEY='my-secret-key'
DEBUG="true"
EMPTY_VAR=
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(content)
        f.name
    yield f.name
    os.unlink(f.name)


def test_parse_basic_key_values(tmp_env_file):
    result = load_env_file(tmp_env_file)
    assert result["APP_ENV"] == "staging"
    assert result["DATABASE_URL"] == "postgres://localhost:5432/mydb"


def test_parse_strips_single_quotes(tmp_env_file):
    result = load_env_file(tmp_env_file)
    assert result["SECRET_KEY"] == "my-secret-key"


def test_parse_strips_double_quotes(tmp_env_file):
    result = load_env_file(tmp_env_file)
    assert result["DEBUG"] == "true"


def test_parse_empty_value(tmp_env_file):
    result = load_env_file(tmp_env_file)
    assert result["EMPTY_VAR"] == ""


def test_parse_ignores_comments(tmp_env_file):
    result = load_env_file(tmp_env_file)
    assert "# Sample env file" not in result
    assert len(result) == 5


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError, match="Env file not found"):
        load_env_file("/nonexistent/path/.env")


def test_invalid_line_raises():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("INVALID_LINE_WITHOUT_EQUALS\n")
        fname = f.name
    try:
        with pytest.raises(ValueError, match="Invalid format"):
            load_env_file(fname)
    finally:
        os.unlink(fname)


def test_empty_key_raises():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("=value_without_key\n")
        fname = f.name
    try:
        with pytest.raises(ValueError, match="Empty key"):
            load_env_file(fname)
    finally:
        os.unlink(fname)
