from .models import Diagnosis, PaymentEvent, RecoveryPlan, RiskScore


def diagnose(payment: PaymentEvent, risk: RiskScore) -> Diagnosis:
    if payment.customer_opted_out:
        return Diagnosis(
            root_cause="customer_opted_out",
            reasoning="Customer has opted out, so ReviveAI must not initiate payment recovery.",
            recommended_action="escalate",
        )

    if payment.failure_type in {"bank_timeout", "technical_error"}:
        return Diagnosis(
            root_cause="temporary_provider_or_bank_failure",
            reasoning="The customer has successful payment history and this failure type is often transient.",
            recommended_action="delayed_retry",
        )

    if payment.failure_type == "checkout_abandonment":
        return Diagnosis(
            root_cause="checkout_drop_off",
            reasoning="The customer showed purchase intent but did not complete checkout.",
            recommended_action="send_recovery_link",
        )

    if payment.failure_type == "expired_method":
        return Diagnosis(
            root_cause="stale_payment_instrument",
            reasoning="Retrying the same instrument is unlikely to work until the customer updates it.",
            recommended_action="send_recovery_link",
        )

    if payment.failure_type == "insufficient_funds":
        return Diagnosis(
            root_cause="customer_funding_issue",
            reasoning="A low-friction payment link is safer than repeated immediate retries.",
            recommended_action="send_recovery_link",
        )

    if risk.priority == "LOW":
        return Diagnosis(
            root_cause="low_recovery_likelihood",
            reasoning="The case has weak recovery signals and should not consume automatic retry budget.",
            recommended_action="escalate",
        )

    return Diagnosis(
        root_cause="issuer_or_mandate_decline",
        reasoning="The failure may recover through a sequenced retry, but needs strict limits.",
        recommended_action="delayed_retry",
    )


def plan_recovery(payment: PaymentEvent, diagnosis: Diagnosis) -> RecoveryPlan:
    if diagnosis.recommended_action == "delayed_retry":
        return RecoveryPlan(
            action="retry_payment",
            delay_minutes=30,
            max_retries=2,
            explanation="Retry once after bank rails settle; escalate if retry budget is exhausted.",
        )

    if diagnosis.recommended_action == "send_recovery_link":
        return RecoveryPlan(
            action="send_payment_link",
            delay_minutes=0,
            max_retries=1,
            explanation="Send a Razorpay payment link so the customer can use a fresh method.",
        )

    return RecoveryPlan(
        action="escalate",
        delay_minutes=0,
        max_retries=0,
        explanation="Stop automation and route the case to a human operator.",
    )
