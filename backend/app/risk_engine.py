from .models import PaymentEvent, RiskScore


FAILURE_WEIGHTS = {
    "bank_timeout": 0.30,
    "technical_error": 0.28,
    "issuer_decline": 0.18,
    "insufficient_funds": 0.10,
    "expired_method": 0.16,
    "mandate_failure": 0.22,
    "checkout_abandonment": 0.24,
}


def score_payment(payment: PaymentEvent) -> RiskScore:
    loyalty = min(payment.previous_successes / 10, 1.0) * 0.25
    failure_penalty = min(payment.previous_failures / 5, 1.0) * 0.18
    amount_signal = 0.12 if payment.amount >= 5000 else 0.06
    recency_signal = 0.10 if payment.last_attempt_minutes <= 60 else 0.03
    subscription_signal = 0.08 if payment.subscription_active else 0.0
    abandonment_signal = 0.08 if payment.checkout_abandoned else 0.0
    failure_signal = FAILURE_WEIGHTS.get(payment.failure_type, 0.08)

    probability = (
        0.12
        + loyalty
        + amount_signal
        + recency_signal
        + subscription_signal
        + abandonment_signal
        + failure_signal
        - failure_penalty
    )
    probability = max(0.02, min(probability, 0.97))

    if probability >= 0.75:
        priority = "HIGH"
    elif probability >= 0.48:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return RiskScore(
        probability=round(probability, 3),
        priority=priority,
        features={
            "loyalty": round(loyalty, 3),
            "failure_signal": round(failure_signal, 3),
            "amount_signal": amount_signal,
            "recency_signal": recency_signal,
            "failure_penalty": round(failure_penalty, 3),
        },
    )
