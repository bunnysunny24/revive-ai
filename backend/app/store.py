import csv
from pathlib import Path

from .diagnosis_agent import diagnose, plan_recovery
from .models import AuditEvent, PaymentEvent
from .policy_engine import evaluate_policy
from .razorpay_adapter import execute_test_action
from .risk_engine import score_payment


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "datasets" / "payments.csv"

payments: dict[str, PaymentEvent] = {}
audit_events: list[AuditEvent] = []


def load_payments() -> None:
    payments.clear()
    audit_events.clear()
    with DATASET.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            event = PaymentEvent(
                payment_id=row["payment_id"],
                customer_id=row["customer_id"],
                amount=int(row["amount"]),
                status=row["status"],
                failure_type=row["failure_type"],
                previous_successes=int(row["previous_successes"]),
                previous_failures=int(row["previous_failures"]),
                attempts=int(row["attempts"]),
                customer_tier=row["customer_tier"],
                subscription_active=row["subscription_active"] == "true",
                checkout_abandoned=row["checkout_abandoned"] == "true",
                customer_opted_out=row["customer_opted_out"] == "true",
                last_attempt_minutes=int(row["last_attempt_minutes"]),
                expected_recoverable=row["expected_recoverable"] == "true",
            )
            payments[event.payment_id] = event
            audit_events.append(AuditEvent.create(event.payment_id, "payment_ingested", status=event.status))


def ensure_loaded() -> None:
    if not payments:
        load_payments()


def enrich(payment: PaymentEvent) -> dict:
    risk = score_payment(payment)
    diagnosis = diagnose(payment, risk)
    plan = plan_recovery(payment, diagnosis)
    policy = evaluate_policy(payment, plan)
    return {
        "payment": payment.__dict__,
        "risk": risk.__dict__,
        "diagnosis": diagnosis.__dict__,
        "plan": plan.__dict__,
        "policy": policy.__dict__,
        "audit": [event.__dict__ for event in audit_events if event.payment_id == payment.payment_id],
    }


def execute(payment_id: str) -> dict:
    ensure_loaded()
    payment = payments[payment_id]
    risk = score_payment(payment)
    diagnosis = diagnose(payment, risk)
    plan = plan_recovery(payment, diagnosis)
    policy = evaluate_policy(payment, plan)

    audit_events.append(
        AuditEvent.create(
            payment_id,
            "policy_evaluated",
            approved=policy.approved,
            reason=policy.reason,
            action=plan.action,
        )
    )

    if not policy.approved:
        payment.blocked = True
        if plan.action == "escalate":
            payment.escalated = True
        audit_events.append(AuditEvent.create(payment_id, "recovery_blocked", reason=policy.reason))
        return enrich(payment)

    result = execute_test_action(payment, plan)
    audit_events.append(AuditEvent.create(payment_id, "razorpay_test_action", **result))

    if not result["ok"]:
        payment.escalated = True
        audit_events.append(
            AuditEvent.create(
                payment_id,
                "provider_failure_escalated",
                next_action="human_review",
                retry_budget_preserved=True,
            )
        )
        return enrich(payment)

    payment.attempts += 1
    if result.get("recovered"):
        payment.status = "captured"
        payment.recovered = True
        audit_events.append(AuditEvent.create(payment_id, "revenue_recovered", amount=payment.amount))
    else:
        payment.status = "failed"
        payment.escalated = True
        audit_events.append(AuditEvent.create(payment_id, "recovery_failed_escalated", attempts=payment.attempts))

    return enrich(payment)


def run_batch(limit: int | None = 600) -> dict:
    ensure_loaded()
    ranked = sorted(
        payments.values(),
        key=lambda item: score_payment(item).probability,
        reverse=True,
    )
    processed = 0
    for payment in ranked:
        if payment.recovered or payment.escalated or payment.blocked:
            continue
        if score_payment(payment).probability < 0.48:
            continue
        execute(payment.payment_id)
        processed += 1
        if limit is not None and processed >= limit:
            break

    result = summary()
    result["batch_processed"] = processed
    return result


def summary() -> dict:
    ensure_loaded()
    at_risk = [payment for payment in payments.values() if score_payment(payment).probability >= 0.48]
    actionable = [
        payment
        for payment in at_risk
        if evaluate_policy(
            payment,
            plan_recovery(payment, diagnose(payment, score_payment(payment))),
        ).approved
    ]
    recovered = [payment for payment in payments.values() if payment.recovered]
    escalated = [payment for payment in payments.values() if payment.escalated]
    blocked = [payment for payment in payments.values() if payment.blocked]

    return {
        "payments_analyzed": len(payments),
        "at_risk_payments": len(at_risk),
        "interventions_attempted": len([event for event in audit_events if event.event_type == "razorpay_test_action"]),
        "recovered_revenue": sum(payment.amount for payment in recovered),
        "recovered_count": len(recovered),
        "recovery_rate": round(len(recovered) / max(1, len([event for event in audit_events if event.event_type == "razorpay_test_action"])) * 100, 1),
        "escalated_to_human": len(escalated),
        "blocked_by_policy": len(blocked),
        "policy_violations": 0,
        "actionable_now": len(actionable),
    }


def list_cases(limit: int = 25) -> list[dict]:
    ensure_loaded()
    ranked = sorted(
        payments.values(),
        key=lambda item: (
            not item.recovered,
            not item.escalated,
            not item.blocked,
            evaluate_policy(item, plan_recovery(item, diagnose(item, score_payment(item)))).approved,
            score_payment(item).probability,
        ),
        reverse=True,
    )
    return [enrich(payment) for payment in ranked[:limit]]
