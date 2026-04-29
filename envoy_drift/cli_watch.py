"""CLI subcommand for watching env files and reporting drift on change."""

import argparse
import sys
from typing import Optional

from envoy_drift.parser import load_env_file
from envoy_drift.comparator import EnvComparator
from envoy_drift.reporter import DriftReporter, OutputFormat
from envoy_drift.watcher import EnvFileWatcher


def build_watch_parser(subparsers=None) -> argparse.ArgumentParser:
    """Build argument parser for the 'watch' subcommand."""
    description = "Watch env files and report drift whenever they change."
    if subparsers is not None:
        parser = subparsers.add_parser("watch", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy-drift watch", description=description)

    parser.add_argument("source", help="Path to source (staging) env file")
    parser.add_argument("target", help="Path to target (production) env file")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="output_format",
        help="Output format for drift report (default: text)",
    )
    return parser


def _on_change_handler(output_format: str):
    """Return a callback that compares two env files and prints a drift report."""

    def handler(source_path: str, target_path: str) -> None:
        source_env = load_env_file(source_path)
        target_env = load_env_file(target_path)
        comparator = EnvComparator(source_env, target_env)
        report = comparator.compare()
        fmt = OutputFormat(output_format)
        reporter = DriftReporter(report, fmt)
        reporter.render()

    return handler


def run_watch_command(args: argparse.Namespace) -> None:
    """Entry point for the watch subcommand."""
    print(
        f"Watching {args.source} and {args.target} "
        f"(interval={args.interval}s) — press Ctrl+C to stop.",
        flush=True,
    )
    handler = _on_change_handler(args.output_format)
    watcher = EnvFileWatcher(
        source_path=args.source,
        target_path=args.target,
        on_change=handler,
        poll_interval=args.interval,
    )
    try:
        watcher.watch()
    except KeyboardInterrupt:
        print("\nWatcher stopped.", file=sys.stderr)
