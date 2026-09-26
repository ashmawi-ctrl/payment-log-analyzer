from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median
from typing import Iterable

from .models import PaymentRecord


TERMINAL_STATUSES = {"success", "failed", "declined", "cancelled", "refunded"}


@dataclass(frozen=True)
class EndpointLatency:
    endpoint: str
    count: int
    p50_ms: float
    p95_ms: float
    max_ms: float


@dataclass(frozen=True)
class StatusConflict:
    transaction_id: str
    terminal_statuses: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    total_records: int
    unique_transactions: int
    status_counts: dict[str, int]
    response_code_counts: dict[str, int]
    endpoint_counts: dict[str, int]
    currency_counts: dict[str, int]
    overall_latency_ms: dict[str, float]
    endpoint_latency: list[EndpointLatency]
    slow_records: int
    terminal_status_conflicts: list[StatusConflict]


def analyze_records(
    records: Iterable[PaymentRecord],
    *,
    slow_threshold_ms: float = 2000,
) -> AnalysisResult:
    rows = list(records)
    if slow_threshold_ms < 0:
        raise ValueError("slow_threshold_ms cannot be negative")

    status_counts = Counter(row.status for row in rows)
    response_code_counts = Counter(row.response_code for row in rows)
    endpoint_counts = Counter(row.endpoint for row in rows)
    currency_counts = Counter(
        row.currency for row in rows if row.currency is not None
    )

    latency_values = [row.latency_ms for row in rows]
    endpoint_values: dict[str, list[float]] = defaultdict(list)
    transaction_statuses: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        endpoint_values[row.endpoint].append(row.latency_ms)
        if row.status in TERMINAL_STATUSES:
            transaction_statuses[row.transaction_id].add(row.status)

    endpoint_latency = [
        EndpointLatency(
            endpoint=endpoint,
            count=len(values),
            p50_ms=round(_percentile(values, 50), 2),
            p95_ms=round(_percentile(values, 95), 2),
            max_ms=round(max(values), 2),
        )
        for endpoint, values in endpoint_values.items()
    ]
    endpoint_latency.sort(key=lambda item: item.p95_ms, reverse=True)

    conflicts = [
        StatusConflict(
            transaction_id=transaction_id,
            terminal_statuses=tuple(sorted(statuses)),
        )
        for transaction_id, statuses in transaction_statuses.items()
        if len(statuses) > 1
    ]
    conflicts.sort(key=lambda item: item.transaction_id)

    overall_latency = (
        {
            "p50": round(median(latency_values), 2),
            "p95": round(_percentile(latency_values, 95), 2),
            "max": round(max(latency_values), 2),
        }
        if latency_values
        else {"p50": 0.0, "p95": 0.0, "max": 0.0}
    )

    return AnalysisResult(
        total_records=len(rows),
        unique_transactions=len({row.transaction_id for row in rows}),
        status_counts=dict(status_counts.most_common()),
        response_code_counts=dict(response_code_counts.most_common()),
        endpoint_counts=dict(endpoint_counts.most_common()),
        currency_counts=dict(currency_counts.most_common()),
        overall_latency_ms=overall_latency,
        endpoint_latency=endpoint_latency,
        slow_records=sum(
            1 for row in rows if row.latency_ms >= slow_threshold_ms
        ),
        terminal_status_conflicts=conflicts,
    )


def result_to_dict(result: AnalysisResult) -> dict[str, object]:
    return {
        "total_records": result.total_records,
        "unique_transactions": result.unique_transactions,
        "status_counts": result.status_counts,
        "response_code_counts": result.response_code_counts,
        "endpoint_counts": result.endpoint_counts,
        "currency_counts": result.currency_counts,
        "overall_latency_ms": result.overall_latency_ms,
        "endpoint_latency": [asdict(item) for item in result.endpoint_latency],
        "slow_records": result.slow_records,
        "terminal_status_conflicts": [
            asdict(item) for item in result.terminal_status_conflicts
        ],
    }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]

    ordered = sorted(values)
    rank = (len(ordered) - 1) * (percentile / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower

    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
