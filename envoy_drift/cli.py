"""Command-line interface for envoy-drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_drift.parser import EnvFileParser
from envoy_drift.comparator import EnvComparator
from envoy_drift.reporter import DriftReporter, OutputFormat


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-drift",
        description="Detect configuration drift between .env files.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Source environment file (e.g. .env.staging)",
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Target environment file (e.g. .env.production)",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if drift is detected",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    for path in (args.source, args.target):
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 2

    source_env = EnvFileParser(args.source).parse()
    target_env = EnvFileParser(args.target).parse()

    report = EnvComparator(source_env, target_env).compare()

    reporter = DriftReporter(fmt=OutputFormat(args.fmt))
    reporter.render(report)

    if args.exit_code and report.has_drift:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
