from pathlib import Path

from paylog.parser import load_records


def test_loads_csv_and_normalizes_values(tmp_path: Path) -> None:
    path = tmp_path / "payments.csv"
    path.write_text(
        "timestamp,transaction_id,status,response_code,endpoint,latency_ms,amount,currency\n"
        "2026-09-26T10:00:00Z,txn_1,SUCCESS,00,/pay,120.5,199.99,egp\n",
        encoding="utf-8",
    )

    records, errors = load_records(path)

    assert errors == []
    assert len(records) == 1
    record = records[0]
    assert record.transaction_id == "txn_1"
    assert record.status == "success"
    assert record.currency == "EGP"
    assert record.latency_ms == 120.5


def test_loads_jsonl_and_reports_bad_line(tmp_path: Path) -> None:
    path = tmp_path / "payments.jsonl"
    path.write_text(
        '{"timestamp":"2026-09-26T10:00:00Z","transaction_id":"txn_1",'
        '"status":"failed","response_code":"51","endpoint":"/pay",'
        '"latency_ms":350}\n'
        '{"broken":\n',
        encoding="utf-8",
    )

    records, errors = load_records(path)

    assert len(records) == 1
    assert len(errors) == 1
    assert "invalid JSON" in errors[0].reason


def test_missing_required_field_becomes_parse_error(tmp_path: Path) -> None:
    path = tmp_path / "payments.csv"
    path.write_text(
        "timestamp,transaction_id,status,response_code,endpoint,latency_ms\n"
        "2026-09-26T10:00:00Z,txn_1,success,00,,120\n",
        encoding="utf-8",
    )

    records, errors = load_records(path)

    assert records == []
    assert len(errors) == 1
    assert "endpoint" in errors[0].reason
