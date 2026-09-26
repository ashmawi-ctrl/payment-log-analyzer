import argparse
from pathlib import Path

from .analyzer import analyze_records
from .parser import load_records
from .report import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="payment-log-analyzer",
        description="Summarize payment/API logs and surface operational anomalies.",
    )
    parser.add_argument("path", help="CSV, JSONL or NDJSON input file")
    parser.add_argument(
        "--slow-ms",
        type=float,
        default=2000,
        help="Latency threshold used to count slow records",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Report format",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum rows shown in Markdown report sections",
    )
    parser.add_argument(
        "--output",
        help="Optional output file. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Print parse errors to stderr after the report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.top < 1:
        raise SystemExit("--top must be at least 1")

    records, errors = load_records(args.path)
    result = analyze_records(records, slow_threshold_ms=args.slow_ms)

    if args.format == "json":
        report = render_json(result, parse_errors=len(errors))
    else:
        report = render_markdown(
            result,
            parse_errors=len(errors),
            top=args.top,
        )

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")

    if args.show_errors and errors:
        import sys

        for error in errors:
            print(
                f"row {error.row_number}: {error.reason}",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
