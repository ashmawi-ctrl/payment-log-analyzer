from datetime import datetime, timezone
from decimal import Decimal

from paylog.analyzer import analyze_records
from paylog.models import PaymentRecord


def record(
    transaction_id: str,
    status: str,
    response_code: str,
    endpoint: str,
    latency_ms: float,
    currency: str = "EGP",
) -> PaymentRecord:
    return PaymentRecord(
        timestamp=datetime(2026, 9, 26, tzinfo=timezone.utc),
        transaction_id=transaction_id,
        status=status,
        response_code=response_code,
        endpoint=endpoint,
        latency_ms=latency_ms,
        amount=Decimal("100"),
        currency=currency,
    )


def test_counts_statuses_codes_and_slow_records() -> None:
    result = analyze_records(
        [
            record("txn_1", "success", "00", "/pay", 100),
            record("txn_2", "failed", "51", "/pay", 2500),
            record("txn_3", "failed", "51", "/refund", 800),
        ],
        slow_threshold_ms=2000,
    )

    assert result.total_records == 3
    assert result.unique_transactions == 3
    assert result.status_counts == {"failed": 2, "success": 1}
    assert result.response_code_counts == {"51": 2, "00": 1}
    assert result.slow_records == 1
    assert result.overall_latency_ms["max"] == 2500


def test_detects_conflicting_terminal_statuses() -> None:
    result = analyze_records(
        [
            record("txn_1", "success", "00", "/status", 100),
            record("txn_1", "failed", "96", "/status", 120),
            record("txn_2", "pending", "P", "/status", 80),
        ]
    )

    assert len(result.terminal_status_conflicts) == 1
    conflict = result.terminal_status_conflicts[0]
    assert conflict.transaction_id == "txn_1"
    assert conflict.terminal_statuses == ("failed", "success")


def test_endpoint_latency_is_sorted_by_p95() -> None:
    result = analyze_records(
        [
            record("txn_1", "success", "00", "/fast", 100),
            record("txn_2", "success", "00", "/slow", 1000),
            record("txn_3", "success", "00", "/slow", 2000),
        ]
    )

    assert result.endpoint_latency[0].endpoint == "/slow"
    assert result.endpoint_latency[0].p95_ms > result.endpoint_latency[1].p95_ms
