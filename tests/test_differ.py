"""Tests for envoy_drift.differ module."""
import pytest
from envoy_drift.differ import EnvDiffer, EnvDiff, ValueDiff


@pytest.fixture
def differ() -> EnvDiffer:
    return EnvDiffer()


def test_no_diff_identical_dicts(differ):
    env = {"FOO": "bar", "BAZ": "qux"}
    result = differ.diff(env, env)
    assert not result.has_differences
    assert result.diffs == []


def test_no_diff_empty_dicts(differ):
    result = differ.diff({}, {})
    assert not result.has_differences


def test_detects_changed_value(differ):
    source = {"FOO": "old"}
    target = {"FOO": "new"}
    result = differ.diff(source, target)
    assert result.has_differences
    assert "FOO" in result.changed_keys
    assert result.diffs[0].is_changed


def test_detects_key_missing_in_target(differ):
    source = {"FOO": "bar", "EXTRA": "only_in_source"}
    target = {"FOO": "bar"}
    result = differ.diff(source, target)
    assert "EXTRA" in result.missing_in_target
    assert "EXTRA" not in result.missing_in_source


def test_detects_key_missing_in_source(differ):
    source = {"FOO": "bar"}
    target = {"FOO": "bar", "EXTRA": "only_in_target"}
    result = differ.diff(source, target)
    assert "EXTRA" in result.missing_in_source
    assert "EXTRA" not in result.missing_in_target


def test_diff_keys_are_sorted(differ):
    source = {"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"}
    target = {"Z_KEY": "x", "A_KEY": "y", "M_KEY": "z"}
    result = differ.diff(source, target)
    keys = [d.key for d in result.diffs]
    assert keys == sorted(keys)


def test_value_diff_describe_changed():
    vd = ValueDiff(key="PORT", source_value="8080", target_value="9090")
    desc = vd.describe()
    assert "PORT" in desc
    assert "8080" in desc
    assert "9090" in desc


def test_value_diff_describe_missing_in_target():
    vd = ValueDiff(key="SECRET", source_value="abc", target_value=None)
    assert vd.is_missing_in_target
    assert "missing in target" in vd.describe()


def test_value_diff_describe_missing_in_source():
    vd = ValueDiff(key="SECRET", source_value=None, target_value="xyz")
    assert vd.is_missing_in_source
    assert "missing in source" in vd.describe()


def test_env_diff_summary_lines(differ):
    source = {"A": "1", "B": "2"}
    target = {"A": "99", "C": "3"}
    result = differ.diff(source, target)
    lines = result.summary_lines()
    assert len(lines) == len(result.diffs)
    assert all(isinstance(line, str) for line in lines)


def test_unchanged_key_not_in_diff(differ):
    source = {"KEEP": "same", "CHANGE": "old"}
    target = {"KEEP": "same", "CHANGE": "new"}
    result = differ.diff(source, target)
    diff_keys = [d.key for d in result.diffs]
    assert "KEEP" not in diff_keys
    assert "CHANGE" in diff_keys
