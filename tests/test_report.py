import json
from datetime import datetime, timezone
from decimal import Decimal

from paylog.analyzer import analyze_records
from paylog.models import PaymentRecord
from paylog.report import render_json, render_markdown


def sample_result():
    record = PaymentRecord(
        timestamp=datetime(2026, 9, 26, tzinfo=timezone.utc),
        transaction_id="txn_1",
        status="failed",
        response_code="51",
        endpoint="/pay",
        latency_ms=2500,
        amount=Decimal("100"),
        currency="EGP",
    )
    return analyze_records([record], slow_threshold_ms=2000)


def test_json_report_is_machine_readable() -> None:
    payload = json.loads(render_json(sample_result(), parse_errors=2))

    assert payload["summary"]["parse_errors"] == 2
    assert payload["summary"]["slow_records"] == 1
    assert payload["response_code_counts"]["51"] == 1


def test_markdown_report_contains_key_sections() -> None:
    report = render_markdown(sample_result(), parse_errors=1)

    assert "# Payment Log Analysis" in report
    assert "## Response codes" in report
    assert "## Slowest endpoints by p95" in report
    assert "Parse errors: **1**" in report
