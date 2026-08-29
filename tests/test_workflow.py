import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.diagnosis_agent import diagnose, plan_recovery
from app.ml_model import features, load_model, predict_probability, score_with_model, train_model
from app.models import AuditEvent, PaymentEvent
from app.policy_engine import evaluate_policy
from app.razorpay_adapter import execute_test_action
from app.risk_engine import score_payment
from app.store import enrich, execute, load_payments, payments


def make_payment(**overrides) -> PaymentEvent:
    data = {
        "payment_id": "TEST001",
        "customer_id": "CUST001",
        "amount": 8499,
        "status": "failed",
        "failure_type": "bank_timeout",
        "previous_successes": 9,
        "previous_failures": 0,
        "attempts": 0,
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
    # -------------------------------------------------------------
    # 1. Risk Engine Tests
    # -------------------------------------------------------------
    def test_good_transient_failure_is_high_priority(self):
        event = make_payment()
        risk = score_payment(event)
        self.assertEqual(risk.priority, "HIGH")
        self.assertGreaterEqual(risk.probability, 0.75)
        self.assertIn("loyalty", risk.features)
        self.assertIn("subscription_signal", risk.features)

    def test_high_failures_lower_priority(self):
        event = make_payment(
            previous_successes=0,
            previous_failures=5,
            failure_type="issuer_decline",
            subscription_active=False,
            amount=499,
            last_attempt_minutes=1440,
        )
        risk = score_payment(event)
        self.assertEqual(risk.priority, "LOW")
        self.assertLess(risk.probability, 0.48)

    # -------------------------------------------------------------
    # 2. Policy Engine Tests (6 Core Gates)
    # -------------------------------------------------------------
    def test_policy_blocks_high_value_payment(self):
        event = make_payment(amount=24999, failure_type="checkout_abandonment", attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)
        self.assertFalse(decision.approved)
        self.assertIn("amount", decision.reason.lower())

    def test_policy_blocks_customer_opt_out(self):
        event = make_payment(customer_opted_out=True, attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)
        self.assertFalse(decision.approved)
        self.assertIn("opted out", decision.reason.lower())

    def test_policy_blocks_retry_cooldown_not_elapsed(self):
        # 10 minutes elapsed < 30 min cooldown
        event = make_payment(last_attempt_minutes=10, attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)
        self.assertFalse(decision.approved)
        self.assertIn("cooldown", decision.reason.lower())

    def test_policy_blocks_retry_budget_exhausted(self):
        # attempts=2 >= max_retries=2
        event = make_payment(attempts=2, last_attempt_minutes=60)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)
        self.assertFalse(decision.approved)
        self.assertIn("budget exhausted", decision.reason.lower())

    def test_policy_blocks_already_recovered_payment(self):
        event = make_payment(recovered=True, status="captured")
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        decision = evaluate_policy(event, plan)
        self.assertFalse(decision.approved)
        self.assertIn("already recovered", decision.reason.lower())

    # -------------------------------------------------------------
    # 3. Diagnosis Agent Tests
    # -------------------------------------------------------------
    def test_diagnosis_checkout_abandonment_recommends_link_and_sms(self):
        event = make_payment(failure_type="checkout_abandonment", checkout_abandoned=True)
        risk = score_payment(event)
        diag = diagnose(event, risk)
        self.assertEqual(diag.recommended_action, "send_recovery_link")
        self.assertEqual(diag.recovery_channel, "sms")
        self.assertIn("checkout", diag.root_cause)

    def test_diagnosis_expired_method_recommends_email(self):
        event = make_payment(failure_type="expired_method")
        risk = score_payment(event)
        diag = diagnose(event, risk)
        self.assertEqual(diag.recommended_action, "send_recovery_link")
        self.assertEqual(diag.recovery_channel, "email")
        self.assertEqual(diag.root_cause, "stale_payment_instrument")

    def test_diagnosis_low_risk_recommends_escalation(self):
        event = make_payment(
            previous_successes=0,
            previous_failures=5,
            failure_type="issuer_decline",
            subscription_active=False,
            amount=499,
            last_attempt_minutes=1440,
        )
        risk = score_payment(event)
        self.assertEqual(risk.priority, "LOW")
        diag = diagnose(event, risk)
        self.assertEqual(diag.recommended_action, "escalate")
        self.assertEqual(diag.recovery_channel, "none")

    # -------------------------------------------------------------
    # 4. Razorpay Adapter Tests
    # -------------------------------------------------------------
    def test_provider_failure_is_reproducible_for_demo(self):
        event = make_payment(payment_id="DEMO_FAIL7", failure_type="technical_error", attempts=0)
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        result = execute_test_action(event, plan)
        self.assertFalse(result["ok"])
        self.assertEqual(result["provider_status"], "api_error")

    def test_payment_link_adapter_generates_short_url(self):
        event = make_payment(payment_id="TEST_LINK_01", failure_type="checkout_abandonment")
        risk = score_payment(event)
        plan = plan_recovery(event, diagnose(event, risk))
        result = execute_test_action(event, plan)
        self.assertTrue(result["ok"])
        self.assertIn("short_url", result["razorpay_object"])
        self.assertTrue(result["razorpay_object"]["short_url"].startswith("https://rzp.io/test/"))

    # -------------------------------------------------------------
    # 5. ML Model Feature Vector & Training Tests
    # -------------------------------------------------------------
    def test_ml_feature_vector_dimension(self):
        event = make_payment()
        vec = features(event)
        # 1 bias + 8 scalars + 7 one-hot failure types = 16 features
        self.assertEqual(len(vec), 16)
        self.assertGreaterEqual(vec[0], 1.0)

    def test_ml_model_train_and_inference(self):
        training_batch = [
            make_payment(payment_id=f"P_{i}", expected_recoverable=(i % 2 == 0))
            for i in range(20)
        ]
        model = train_model(training_batch, epochs=10)
        self.assertEqual(model["model_type"], "pure_python_logistic_regression")
        self.assertEqual(len(model["weights"]), 16)
        prob = predict_probability(training_batch[0], model["weights"])
        self.assertTrue(0.0 <= prob <= 1.0)

    # -------------------------------------------------------------
    # 6. End-to-End Store Execution & Audit Trail Tests
    # -------------------------------------------------------------
    def test_end_to_end_execute_recovers_and_creates_audit_trail(self):
        load_payments()
        demo_event = make_payment(
            payment_id="DEMO_SUCCESS",
            failure_type="bank_timeout",
            previous_successes=10,
            last_attempt_minutes=60,
            amount=1999,
            attempts=0,
        )
        payments[demo_event.payment_id] = demo_event

        res = execute("DEMO_SUCCESS")
        self.assertTrue(res["payment"]["recovered"])
        self.assertEqual(res["payment"]["status"], "captured")
        self.assertTrue(len(res["audit"]) >= 2)
        event_types = [a["event_type"] for a in res["audit"]]
        self.assertIn("policy_evaluated", event_types)
    def test_webhook_ingestion_adds_payment_and_audit(self):
        from backend.app.store import ingest_webhook_payment
        load_payments()
        webhook_data = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_wh_test_99",
                        "amount": 350000,
                        "status": "failed",
                        "error_reason": "bank_timeout",
                        "notes": {
                            "customer_id": "cust_vip_wh",
                            "customer_tier": "platinum"
                        }
                    }
                }
            }
        }
        enriched = ingest_webhook_payment(webhook_data)
        self.assertEqual(enriched["payment"]["payment_id"], "pay_wh_test_99")
        self.assertEqual(enriched["payment"]["amount"], 3500)
        self.assertEqual(enriched["payment"]["customer_tier"], "platinum")
        self.assertTrue(any(a["event_type"] == "razorpay_webhook_ingested" for a in enriched["audit"]))


if __name__ == "__main__":
    unittest.main()

