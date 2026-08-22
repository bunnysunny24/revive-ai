import csv
import threading
from collections import defaultdict
from pathlib import Path

from .diagnosis_agent import diagnose, plan_recovery
from .models import AuditEvent, PaymentEvent
from .policy_engine import evaluate_policy
from .razorpay_adapter import execute_test_action
from .risk_engine import score_payment


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "datasets" / "payments.csv"

# Global state protected by a re-entrant thread lock
_lock = threading.RLock()
payments: dict[str, PaymentEvent] = {}
audit_events: list[AuditEvent] = []
_audit_by_payment: dict[str, list[AuditEvent]] = defaultdict(list)


def load_payments() -> None:
    with _lock:
        payments.clear()
        audit_events.clear()
        _audit_by_payment.clear()

        if not DATASET.exists():
            return

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
                    subscription_active=row["subscription_active"].lower() in {"true", "1", "yes"},
                    checkout_abandoned=row["checkout_abandoned"].lower() in {"true", "1", "yes"},
                    customer_opted_out=row["customer_opted_out"].lower() in {"true", "1", "yes"},
                    last_attempt_minutes=int(row["last_attempt_minutes"]),
                    expected_recoverable=row["expected_recoverable"].lower() in {"true", "1", "yes"},
                )
                payments[event.payment_id] = event
                ingest_audit = AuditEvent.create(event.payment_id, "payment_ingested", status=event.status)
                audit_events.append(ingest_audit)
                _audit_by_payment[event.payment_id].append(ingest_audit)


def ensure_loaded() -> None:
    with _lock:
        if not payments:
            load_payments()


def enrich(payment: PaymentEvent) -> dict:
    with _lock:
        risk = score_payment(payment)
        diagnosis = diagnose(payment, risk)
        plan = plan_recovery(payment, diagnosis)
        policy = evaluate_policy(payment, plan)
        audit_list = [event.__dict__ for event in _audit_by_payment.get(payment.payment_id, [])]
        return {
            "payment": payment.__dict__,
            "risk": risk.__dict__,
            "diagnosis": diagnosis.__dict__,
            "plan": plan.__dict__,
            "policy": policy.__dict__,
            "audit": audit_list,
        }


def execute(payment_id: str) -> dict:
    with _lock:
        ensure_loaded()
        if payment_id not in payments:
            raise KeyError(f"Payment {payment_id} not found")

        payment = payments[payment_id]
        risk = score_payment(payment)
        diagnosis = diagnose(payment, risk)
        plan = plan_recovery(payment, diagnosis)
        policy = evaluate_policy(payment, plan)

        policy_audit = AuditEvent.create(
            payment_id,
            "policy_evaluated",
            approved=policy.approved,
            reason=policy.reason,
            action=plan.action,
            recovery_channel=plan.recovery_channel,
        )
        audit_events.append(policy_audit)
        _audit_by_payment[payment_id].append(policy_audit)

        if not policy.approved:
            payment.blocked = True
            if plan.action == "escalate":
                payment.escalated = True
            block_audit = AuditEvent.create(payment_id, "recovery_blocked", reason=policy.reason)
            audit_events.append(block_audit)
            _audit_by_payment[payment_id].append(block_audit)
            return enrich(payment)

        result = execute_test_action(payment, plan)
        action_audit = AuditEvent.create(payment_id, "razorpay_test_action", **result)
        audit_events.append(action_audit)
        _audit_by_payment[payment_id].append(action_audit)

        if not result.get("ok"):
            payment.escalated = True
            fail_audit = AuditEvent.create(
                payment_id,
                "provider_failure_escalated",
                next_action="human_review",
                retry_budget_preserved=True,
                error=result.get("message", "Provider error"),
            )
            audit_events.append(fail_audit)
            _audit_by_payment[payment_id].append(fail_audit)
            return enrich(payment)

        payment.attempts += 1
        payment.recovery_channel = plan.recovery_channel
        if result.get("recovered"):
            payment.status = "captured"
            payment.recovered = True
            rec_audit = AuditEvent.create(
                payment_id,
                "revenue_recovered",
                amount=payment.amount,
                channel=plan.recovery_channel,
            )
            audit_events.append(rec_audit)
            _audit_by_payment[payment_id].append(rec_audit)
        else:
            payment.status = "failed"
            payment.escalated = True
            fail_rec_audit = AuditEvent.create(
                payment_id,
                "recovery_failed_escalated",
                attempts=payment.attempts,
                channel=plan.recovery_channel,
            )
            audit_events.append(fail_rec_audit)
            _audit_by_payment[payment_id].append(fail_rec_audit)

        return enrich(payment)


def run_batch(limit: int | None = 600) -> dict:
    with _lock:
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

        res = summary()
        res["batch_processed"] = processed
        return res


def summary() -> dict:
    with _lock:
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
        action_events = [event for event in audit_events if event.event_type == "razorpay_test_action"]

        channel_breakdown = defaultdict(lambda: {"recovered_count": 0, "recovered_amount": 0})
        for p in recovered:
            ch = p.recovery_channel or "auto_retry"
            channel_breakdown[ch]["recovered_count"] += 1
            channel_breakdown[ch]["recovered_amount"] += p.amount

        return {
            "payments_analyzed": len(payments),
            "at_risk_payments": len(at_risk),
            "interventions_attempted": len(action_events),
            "recovered_revenue": sum(payment.amount for payment in recovered),
            "recovered_count": len(recovered),
            "recovery_rate": round(len(recovered) / max(1, len(action_events)) * 100, 1),
            "escalated_to_human": len(escalated),
            "blocked_by_policy": len(blocked),
            "policy_violations": 0,
            "actionable_now": len(actionable),
            "channel_breakdown": dict(channel_breakdown),
        }


def list_cases(limit: int = 50, filter_type: str | None = None) -> list[dict]:
    with _lock:
        ensure_loaded()
        items = list(payments.values())
        if filter_type == "actionable":
            items = [
                p for p in items
                if not p.recovered and not p.escalated and not p.blocked
                and evaluate_policy(p, plan_recovery(p, diagnose(p, score_payment(p)))).approved
            ]
        elif filter_type == "recovered":
            items = [p for p in items if p.recovered]
        elif filter_type == "escalated":
            items = [p for p in items if p.escalated]
        elif filter_type == "blocked":
            items = [p for p in items if p.blocked]

        ranked = sorted(
            items,
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


def list_recent_audits(limit: int = 100) -> list[dict]:
    with _lock:
        ensure_loaded()
        return [event.__dict__ for event in reversed(audit_events[-limit:])]
