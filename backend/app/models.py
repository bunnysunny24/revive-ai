from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PaymentEvent:
    payment_id: str
    customer_id: str
    amount: int
    status: str
    failure_type: str
    previous_successes: int
    previous_failures: int
    attempts: int
    customer_tier: str
    subscription_active: bool
    checkout_abandoned: bool
    customer_opted_out: bool
    last_attempt_minutes: int
    expected_recoverable: bool
    recovered: bool = False
    escalated: bool = False
    blocked: bool = False
    recovery_channel: str = ""


@dataclass
class RiskScore:
    probability: float
    priority: str
    features: dict[str, float]


@dataclass
class Diagnosis:
    root_cause: str
    reasoning: str
    recommended_action: str
    recovery_channel: str = "auto_retry"


@dataclass
class RecoveryPlan:
    action: str
    delay_minutes: int
    max_retries: int
    explanation: str
    recovery_channel: str = "auto_retry"


@dataclass
class PolicyDecision:
    approved: bool
    reason: str


@dataclass
class AuditEvent:
    timestamp: str
    payment_id: str
    event_type: str
    detail: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, payment_id: str, event_type: str, **detail: Any) -> "AuditEvent":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            payment_id=payment_id,
            event_type=event_type,
            detail=detail,
        )
