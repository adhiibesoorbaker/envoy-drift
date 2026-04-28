"""CLI sub-commands for snapshot management (save / list / diff)."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy_drift.comparator import EnvComparator
from envoy_drift.parser import load_env_file
from envoy_drift.reporter import DriftReporter, OutputFormat
from envoy_drift.snapshot import SnapshotManager


def build_snapshot_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register *snapshot* sub-commands onto *parent* sub-parsers."""
    snap = parent.add_parser("snapshot", help="Manage drift snapshots")
    sub = snap.add_subparsers(dest="snap_cmd", required=True)

    # snapshot save
    save_p = sub.add_parser("save", help="Save current drift to a snapshot file")
    save_p.add_argument("source", help="Source .env file (e.g. staging)")
    save_p.add_argument("target", help="Target .env file (e.g. production)")
    save_p.add_argument("--label", default=None, help="Optional snapshot label")
    save_p.add_argument("--dir", default=".envoy_snapshots", dest="snapshot_dir")

    # snapshot list
    list_p = sub.add_parser("list", help="List saved snapshots")
    list_p.add_argument("--dir", default=".envoy_snapshots", dest="snapshot_dir")

    # snapshot show
    show_p = sub.add_parser("show", help="Show a saved snapshot as a drift report")
    show_p.add_argument("snapshot_file", help="Path to snapshot JSON file")
    show_p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
    )


def run_snapshot_command(args: argparse.Namespace) -> int:
    """Dispatch snapshot sub-command; return exit code."""
    manager = SnapshotManager(snapshot_dir=getattr(args, "snapshot_dir", ".envoy_snapshots"))

    if args.snap_cmd == "save":
        source_env = load_env_file(args.source)
        target_env = load_env_file(args.target)
        report = EnvComparator(source_env, target_env).compare()
        path = manager.save(report, label=args.label)
        print(f"Snapshot saved: {path}")
        return 0

    if args.snap_cmd == "list":
        snapshots = manager.list_snapshots()
        if not snapshots:
            print("No snapshots found.")
        else:
            for s in snapshots:
                print(s)
        return 0

    if args.snap_cmd == "show":
        report = manager.load(args.snapshot_file)
        fmt = OutputFormat(args.format)
        reporter = DriftReporter(report, output_format=fmt)
        reporter.render()
        return 1 if report.has_drift else 0

    print(f"Unknown snapshot command: {args.snap_cmd}", file=sys.stderr)
    return 2
