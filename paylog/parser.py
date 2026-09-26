import csv
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from .models import ParseError, PaymentRecord


REQUIRED_FIELDS = {
    "timestamp",
    "transaction_id",
    "status",
    "response_code",
    "endpoint",
    "latency_ms",
}


def load_records(path: str | Path) -> tuple[list[PaymentRecord], list[ParseError]]:
    """Load CSV or JSONL payment logs and return parsed records plus row errors."""
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix == ".csv":
        rows = _read_csv(source)
    elif suffix in {".jsonl", ".ndjson"}:
        rows = _read_jsonl(source)
    else:
        raise ValueError("supported formats are .csv, .jsonl and .ndjson")

    records: list[PaymentRecord] = []
    errors: list[ParseError] = []

    for row_number, row in rows:
        try:
            records.append(parse_record(row))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(
                ParseError(
                    row_number=row_number,
                    reason=str(exc),
                    raw=row,
                )
            )

    return records, errors


def parse_record(row: dict[str, object]) -> PaymentRecord:
    parse_error = row.get("__parse_error__")
    if parse_error:
        raise ValueError(str(parse_error))

    missing = sorted(field for field in REQUIRED_FIELDS if _is_blank(row.get(field)))
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    timestamp = _parse_timestamp(str(row["timestamp"]))
    latency_ms = _parse_latency(row["latency_ms"])
    amount = _parse_amount(row.get("amount"))

    currency_value = row.get("currency")
    currency = None if _is_blank(currency_value) else str(currency_value).upper()

    return PaymentRecord(
        timestamp=timestamp,
        transaction_id=str(row["transaction_id"]).strip(),
        status=str(row["status"]).strip().lower(),
        response_code=str(row["response_code"]).strip(),
        endpoint=str(row["endpoint"]).strip(),
        latency_ms=latency_ms,
        amount=amount,
        currency=currency,
    )


def _read_csv(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return

        for row_number, row in enumerate(reader, start=2):
            yield row_number, dict(row)


def _read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                yield row_number, {"__parse_error__": f"invalid JSON: {exc.msg}"}
                continue

            if not isinstance(value, dict):
                yield row_number, {"__parse_error__": "JSON line must be an object"}
                continue

            yield row_number, value


def _parse_timestamp(value: str) -> datetime:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def _parse_latency(value: object) -> float:
    try:
        latency = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid latency_ms: {value}") from exc

    if latency < 0:
        raise ValueError("latency_ms cannot be negative")

    return latency


def _parse_amount(value: object) -> Decimal | None:
    if _is_blank(value):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid amount: {value}") from exc


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""
