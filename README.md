# Payment Log Analyzer

A command-line tool for turning payment/API logs into a compact operational report.

I built this around the kind of production investigation where hundreds or thousands of transaction records need to be reduced into a few useful questions:

- which response codes are failing most often?
- which endpoints are slow?
- are some transactions moving between conflicting terminal states?
- how many records are malformed or incomplete?
- what are the p50 / p95 / max latencies?
- which currencies and statuses are actually present in the data?

The project intentionally works with plain CSV and JSON Lines files so it can be used against exported logs without requiring a database or external service.

Current functionality is being added in small, testable pieces.
