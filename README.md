# Payment Log Analyzer

[![quality](https://github.com/ashmawi-ctrl/payment-log-analyzer/actions/workflows/quality.yml/badge.svg)](https://github.com/ashmawi-ctrl/payment-log-analyzer/actions/workflows/quality.yml)

A command-line tool for turning payment/API logs into a compact operational report.

I built this around a common production-support problem: a large log export may contain hundreds or thousands of records, but the useful questions are usually much smaller.

- Which response codes are failing most often?
- Which endpoints have the worst latency?
- How many transactions are slow?
- Are any transaction IDs showing conflicting terminal states?
- How many rows are malformed or incomplete?
- What status/currency mix is actually present in the export?

The tool accepts CSV, JSONL, or NDJSON and produces either Markdown for humans or JSON for another system.

## What it detects

- status distribution
- response-code frequency
- endpoint request counts
- currency distribution
- overall p50 / p95 / max latency
- per-endpoint p50 / p95 / max latency
- configurable slow-request count
- conflicting terminal statuses for the same transaction ID
- malformed input rows without stopping the entire analysis

## Example input

The expected fields are:

```text
timestamp
transaction_id
status
response_code
endpoint
latency_ms
amount          optional
currency        optional
```

Example CSV:

```csv
timestamp,transaction_id,status,response_code,endpoint,latency_ms,amount,currency
2026-09-26T09:00:01Z,txn_1001,success,00,/v2/payments,185,450.00,EGP
2026-09-26T09:00:04Z,txn_1002,failed,51,/v2/payments,310,1200.00,EGP
2026-09-26T09:00:07Z,txn_1003,pending,PENDING,/v2/transfers/tx_1003,2450,800.00,EGP
```

A larger sample is available at [examples/sample-payments.csv](examples/sample-payments.csv).

## Install

Python 3.11+ is required.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

## Analyze a file

Markdown report:

```bash
payment-log-analyzer examples/sample-payments.csv
```

Use a different slow-request threshold:

```bash
payment-log-analyzer examples/sample-payments.csv --slow-ms 1500
```

Write the report to a file:

```bash
payment-log-analyzer examples/sample-payments.csv \
  --output report.md
```

Generate machine-readable JSON:

```bash
payment-log-analyzer examples/sample-payments.csv \
  --format json \
  --output report.json
```

Show malformed-row details:

```bash
payment-log-analyzer exported.jsonl --show-errors
```

## Example Markdown report

For a real input file, the report has sections like:

```text
Payment Log Analysis
  Summary
  Status counts
  Response codes
  Slowest endpoints by p95
  Terminal status conflicts
```

The CLI intentionally reports parse errors separately instead of failing the entire run because one exported row is malformed.

## Terminal status conflicts

The analyzer treats these as terminal states:

```text
success
failed
declined
cancelled
refunded
```

If the same transaction ID appears with more than one terminal state, it is reported.

For example:

```text
txn_1004 -> failed, success
```

That does **not** automatically mean the payment platform is wrong. Logs may represent retries, asynchronous reconciliation, or events from different components. The conflict is a signal for investigation, not a final diagnosis.

## Latency calculation

Latency is calculated from the `latency_ms` field in each record.

The report includes:

- p50
- p95
- maximum
- per-endpoint latency
- count above the `--slow-ms` threshold

Percentiles use linear interpolation over the sorted sample. This is appropriate for quick log inspection; it is not intended to replace production observability tooling.

## CSV and JSONL parsing

CSV files use the header row as field names.

JSONL / NDJSON expects one JSON object per line:

```json
{"timestamp":"2026-09-26T09:00:01Z","transaction_id":"txn_1001","status":"success","response_code":"00","endpoint":"/v2/payments","latency_ms":185,"amount":450,"currency":"EGP"}
```

Invalid lines are collected as parse errors while valid records continue through the analyzer.

## Project structure

```text
paylog/
  analyzer.py   aggregations, percentiles and conflict detection
  cli.py        command-line entry point
  models.py     typed records and parse errors
  parser.py     CSV / JSONL parsing and normalization
  report.py     Markdown and JSON output

tests/
  test_analyzer.py
  test_parser.py
  test_report.py
```

## Quality checks

```bash
ruff check .
pytest
```

The same checks run in GitHub Actions on pushes and pull requests.

## Scope

This tool is intentionally offline and read-only. It analyzes exported logs and does not connect to payment providers or modify transaction state.

Possible future improvements:

- time-window comparisons
- response-code groups and custom mappings
- CSV export for top failures
- recurring-transaction analysis
- correlation-ID grouping
- HTML report
- streaming mode for very large exports

## License

MIT
