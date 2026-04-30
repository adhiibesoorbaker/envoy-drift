"""Integration hook: wires baseline sub-commands into the main envoy-drift CLI.

This module is imported by envoy_drift/cli.py to extend the root parser
with the 'baseline' sub-command group.
"""

from __future__ import annotations

import argparse

from envoy_drift.cli_baseline import build_baseline_parser, run_baseline_command


def register(subparsers: argparse._SubParsersAction, dispatch: dict) -> None:  # type: ignore[type-arg]
    """Register the baseline command group.

    Args:
        subparsers: The root CLI subparsers action to attach to.
        dispatch: Mutable dict mapping command names to handler callables.
    """
    build_baseline_parser(subparsers)
    dispatch["baseline"] = run_baseline_command


__all__ = ["register"]
