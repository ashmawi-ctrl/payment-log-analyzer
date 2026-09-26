from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PaymentRecord:
    timestamp: datetime
    transaction_id: str
    status: str
    response_code: str
    endpoint: str
    latency_ms: float
    amount: Decimal | None
    currency: str | None


@dataclass(frozen=True)
class ParseError:
    row_number: int
    reason: str
    raw: dict[str, object]
