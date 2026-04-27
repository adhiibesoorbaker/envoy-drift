"""Tests for envoy_drift.filters."""

import pytest

from envoy_drift.filters import DriftFilter, build_filter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def glob_filter() -> DriftFilter:
    return build_filter(["SECRET_*", "*_TOKEN", "DEBUG"])


@pytest.fixture()
def regex_filter() -> DriftFilter:
    return build_filter([r"SECRET_\w+", r".*_TOKEN"], use_regex=True)


# ---------------------------------------------------------------------------
# Glob pattern tests
# ---------------------------------------------------------------------------

def test_glob_excludes_prefix_match(glob_filter: DriftFilter) -> None:
    assert glob_filter.should_exclude("SECRET_KEY") is True


def test_glob_excludes_suffix_match(glob_filter: DriftFilter) -> None:
    assert glob_filter.should_exclude("AUTH_TOKEN") is True


def test_glob_excludes_exact_match(glob_filter: DriftFilter) -> None:
    assert glob_filter.should_exclude("DEBUG") is True


def test_glob_does_not_exclude_unmatched_key(glob_filter: DriftFilter) -> None:
    assert glob_filter.should_exclude("DATABASE_URL") is False


def test_filter_keys_removes_excluded(glob_filter: DriftFilter) -> None:
    keys = ["DATABASE_URL", "SECRET_KEY", "PORT", "AUTH_TOKEN"]
    result = glob_filter.filter_keys(keys)
    assert result == ["DATABASE_URL", "PORT"]


def test_apply_to_env_removes_excluded_keys(glob_filter: DriftFilter) -> None:
    env = {"DATABASE_URL": "postgres://", "SECRET_KEY": "abc", "PORT": "5432"}
    result = glob_filter.apply_to_env(env)
    assert result == {"DATABASE_URL": "postgres://", "PORT": "5432"}


def test_apply_to_env_returns_copy(glob_filter: DriftFilter) -> None:
    env = {"DATABASE_URL": "postgres://"}
    result = glob_filter.apply_to_env(env)
    result["NEW_KEY"] = "value"
    assert "NEW_KEY" not in env


# ---------------------------------------------------------------------------
# Regex pattern tests
# ---------------------------------------------------------------------------

def test_regex_excludes_matching_key(regex_filter: DriftFilter) -> None:
    assert regex_filter.should_exclude("SECRET_DB") is True


def test_regex_excludes_token_suffix(regex_filter: DriftFilter) -> None:
    assert regex_filter.should_exclude("GITHUB_TOKEN") is True


def test_regex_does_not_exclude_partial_match(regex_filter: DriftFilter) -> None:
    # 'SECRET_' alone doesn't match r'SECRET_\w+' (needs at least one word char after)
    assert regex_filter.should_exclude("SECRET_") is False


# ---------------------------------------------------------------------------
# build_filter helper
# ---------------------------------------------------------------------------

def test_build_filter_empty_patterns() -> None:
    f = build_filter()
    assert f.should_exclude("ANY_KEY") is False


def test_build_filter_add_pattern_after_creation() -> None:
    f = build_filter(["EXISTING_*"])
    f.add_pattern("NEW_*")
    assert f.should_exclude("NEW_VALUE") is True
