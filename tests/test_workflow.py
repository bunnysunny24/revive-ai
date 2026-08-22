import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.diagnosis_agent import diagnose, plan_recovery
from app.models import PaymentEvent
from app.policy_engine import evaluate_policy
from app.razorpay_adapter import execute_test_action
from app.risk_engine import score_payment


def payment(**overrides):
    data = {
        "payment_id": "TEST001",
        "customer_id": "CUST001",
        "amount": 8499,
        "status": "failed",
        "failure_type": "bank_timeout",
        "previous_successes": 9,
        "previous_failures": 0,
        "attempts": 1,
        "customer_tier": "vip",
        "subscription_active": True,
        "checkout_abandoned": False,
        "customer_opted_out": False,
        "last_attempt_minutes": 45,
        "expected_recoverable": True,
    }
    data.update(overrides)
    return PaymentEvent(**data)


class WorkflowTests(unittest.TestCase):
    def test_good_transient_failure_is_high_priority(self):
        event = payment()
        risk = score_payment(event)

        self.assertEqual(risk.priority, "HIGH")
        self.assertGreaterEqual(risk.probability, 0.75)

    def test_policy_blocks_high_value_payment(self):
        event = payment(amount=24999, failure_type="checkout_abandonment", attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)

        self.assertFalse(decision.approved)
        self.assertIn("amount", decision.reason.lower())

    def test_policy_blocks_customer_opt_out(self):
        event = payment(customer_opted_out=True, attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)

        self.assertFalse(decision.approved)
        self.assertIn("opted out", decision.reason.lower())

    def test_provider_failure_is_reproducible_for_demo(self):
        event = payment(payment_id="DEMO_FAIL7", failure_type="technical_error", attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        result = execute_test_action(event, plan)

        self.assertFalse(result["ok"])
        self.assertEqual(result["provider_status"], "api_error")


if __name__ == "__main__":
    unittest.main()
