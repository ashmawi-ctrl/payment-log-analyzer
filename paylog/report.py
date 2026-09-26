import json
from dataclasses import asdict

from .analyzer import AnalysisResult


def render_json(result: AnalysisResult, *, parse_errors: int = 0) -> str:
    payload = {
        "summary": {
            "total_records": result.total_records,
            "unique_transactions": result.unique_transactions,
            "parse_errors": parse_errors,
            "slow_records": result.slow_records,
        },
        "status_counts": result.status_counts,
        "response_code_counts": result.response_code_counts,
        "endpoint_counts": result.endpoint_counts,
        "currency_counts": result.currency_counts,
        "overall_latency_ms": result.overall_latency_ms,
        "endpoint_latency": [asdict(item) for item in result.endpoint_latency],
        "terminal_status_conflicts": [
            asdict(item) for item in result.terminal_status_conflicts
        ],
    }
    return json.dumps(payload, indent=2)


def render_markdown(
    result: AnalysisResult,
    *,
    parse_errors: int = 0,
    top: int = 10,
) -> str:
    lines = [
        "# Payment Log Analysis",
        "",
        "## Summary",
        "",
        f"- Records analyzed: **{result.total_records}**",
        f"- Unique transactions: **{result.unique_transactions}**",
        f"- Parse errors: **{parse_errors}**",
        f"- Slow records: **{result.slow_records}**",
        f"- Overall p50 latency: **{result.overall_latency_ms['p50']} ms**",
        f"- Overall p95 latency: **{result.overall_latency_ms['p95']} ms**",
        f"- Maximum latency: **{result.overall_latency_ms['max']} ms**",
        "",
        "## Status counts",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]

    lines.extend(
        f"| {status} | {count} |"
        for status, count in list(result.status_counts.items())[:top]
    )

    lines.extend(
        [
            "",
            "## Response codes",
            "",
            "| Response code | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(
        f"| {code} | {count} |"
        for code, count in list(result.response_code_counts.items())[:top]
    )

    lines.extend(
        [
            "",
            "## Slowest endpoints by p95",
            "",
            "| Endpoint | Requests | p50 ms | p95 ms | max ms |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    lines.extend(
        (
            f"| {item.endpoint} | {item.count} | "
            f"{item.p50_ms} | {item.p95_ms} | {item.max_ms} |"
        )
        for item in result.endpoint_latency[:top]
    )

    lines.extend(["", "## Terminal status conflicts", ""])

    if result.terminal_status_conflicts:
        lines.extend(
            f"- `{item.transaction_id}`: {', '.join(item.terminal_statuses)}"
            for item in result.terminal_status_conflicts[:top]
        )
    else:
        lines.append("No conflicting terminal statuses detected.")

    return "\n".join(lines) + "\n"
