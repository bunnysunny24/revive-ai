from datetime import datetime, timezone

from .models import PaymentEvent, RecoveryPlan


def execute_test_action(payment: PaymentEvent, plan: RecoveryPlan) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    if payment.failure_type == "technical_error" and payment.payment_id.endswith("7"):
        return {
            "ok": False,
            "provider_status": "api_error",
            "message": "Simulated Razorpay test API timeout.",
            "recovery_channel": plan.recovery_channel,
            "timestamp": timestamp,
        }

    success_map = {
        "bank_timeout": 0.82,
        "technical_error": 0.76,
        "checkout_abandonment": 0.58,
        "expired_method": 0.46,
        "issuer_decline": 0.38,
        "mandate_failure": 0.51,
        "insufficient_funds": 0.34,
    }
    threshold = int(success_map.get(payment.failure_type, 0.25) * 100)
    deterministic_roll = sum(ord(ch) for ch in payment.payment_id) % 100
    recovered = deterministic_roll < threshold

    if recovered:
        provider_status = "captured"
        message = "Recovery action succeeded in Razorpay test mode."
    else:
        provider_status = "failed"
        message = "Recovery action completed but payment was not recovered."

    razorpay_object = {
        "id": "rzp_test_" + payment.payment_id.lower(),
        "mode": "test",
        "action": plan.action,
    }

    if plan.action == "send_payment_link":
        razorpay_object["short_url"] = f"https://rzp.io/test/{payment.payment_id.lower()}"
        razorpay_object["channel"] = plan.recovery_channel

    return {
        "ok": True,
        "provider_status": provider_status,
        "recovered": recovered,
        "message": message,
        "recovery_channel": plan.recovery_channel,
        "timestamp": timestamp,
        "razorpay_object": razorpay_object,
    }
