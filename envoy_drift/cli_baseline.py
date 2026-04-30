"""CLI sub-commands for baseline management in envoy-drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_drift.baseline import BaselineManager, DEFAULT_BASELINE_DIR
from envoy_drift.parser import load_env_file
from envoy_drift.comparator import EnvComparator
from envoy_drift.reporter import DriftReporter, OutputFormat


def build_baseline_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register 'baseline' sub-command onto an existing subparsers action."""
    p = parent.add_parser("baseline", help="Manage env baselines")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    # save
    save_p = sub.add_parser("save", help="Save current env as a baseline")
    save_p.add_argument("env_file", help="Path to .env file")
    save_p.add_argument("name", help="Baseline name")
    save_p.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    # compare
    cmp_p = sub.add_parser("compare", help="Compare env file against a baseline")
    cmp_p.add_argument("env_file", help="Path to current .env file")
    cmp_p.add_argument("name", help="Baseline name to compare against")
    cmp_p.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")
    cmp_p.add_argument("--format", choices=["text", "json"], default="text")

    # list
    list_p = sub.add_parser("list", help="List saved baselines")
    list_p.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    # delete
    del_p = sub.add_parser("delete", help="Delete a baseline")
    del_p.add_argument("name", help="Baseline name")
    del_p.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    return p


def run_baseline_command(args: argparse.Namespace) -> int:
    """Dispatch baseline sub-commands. Returns exit code."""
    manager = BaselineManager(baseline_dir=args.baseline_dir)

    if args.baseline_cmd == "save":
        env = load_env_file(args.env_file)
        path = manager.save(env, args.name)
        print(f"Baseline '{args.name}' saved to {path}")
        return 0

    if args.baseline_cmd == "list":
        baselines = manager.list_baselines()
        if not baselines:
            print("No baselines saved.")
        else:
            for name in baselines:
                meta = manager.metadata(name)
                print(f"  {name}  (saved: {meta['saved_at']})")
        return 0

    if args.baseline_cmd == "delete":
        deleted = manager.delete(args.name)
        if deleted:
            print(f"Baseline '{args.name}' deleted.")
            return 0
        print(f"Baseline '{args.name}' not found.", file=sys.stderr)
        return 1

    if args.baseline_cmd == "compare":
        current_env = load_env_file(args.env_file)
        baseline_env = manager.load(args.name)
        comparator = EnvComparator(baseline_env, current_env)
        report = comparator.compare()
        fmt = OutputFormat(args.format)
        reporter = DriftReporter(report, output_format=fmt)
        reporter.render()
        return 1 if report.has_drift else 0

    return 1
