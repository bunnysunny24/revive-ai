from .models import Diagnosis, PaymentEvent, RecoveryPlan, RiskScore


def diagnose(payment: PaymentEvent, risk: RiskScore) -> Diagnosis:
    if payment.customer_opted_out:
        return Diagnosis(
            root_cause="customer_opted_out",
            reasoning="Customer has opted out of recovery contact. ReviveAI must not initiate automated recovery.",
            recommended_action="escalate",
            recovery_channel="none",
        )

    if payment.failure_type in {"bank_timeout", "technical_error"}:
        history = f"{payment.previous_successes} successful payments" if payment.previous_successes else "no prior history"
        return Diagnosis(
            root_cause="temporary_provider_or_bank_failure",
            reasoning=(
                f"Customer has {history} and this {payment.failure_type.replace('_', ' ')} "
                f"is often transient. Amount: INR {payment.amount:,}. "
                f"A delayed retry after rails settle has high recovery probability ({risk.probability:.0%})."
            ),
            recommended_action="delayed_retry",
            recovery_channel="auto_retry",
        )

    if payment.failure_type == "checkout_abandonment":
        tier_note = f" ({payment.customer_tier} tier customer)" if payment.customer_tier != "new" else ""
        return Diagnosis(
            root_cause="checkout_drop_off",
            reasoning=(
                f"Customer{tier_note} showed purchase intent for INR {payment.amount:,} "
                f"but did not complete checkout. A recovery link via SMS or email "
                f"re-engages intent without friction."
            ),
            recommended_action="send_recovery_link",
            recovery_channel="sms",
        )

    if payment.failure_type == "expired_method":
        return Diagnosis(
            root_cause="stale_payment_instrument",
            reasoning=(
                f"The payment instrument has expired. Retrying the same card will fail again. "
                f"A fresh payment link lets the customer use an updated method. "
                f"Amount: INR {payment.amount:,}."
            ),
            recommended_action="send_recovery_link",
            recovery_channel="email",
        )

    if payment.failure_type == "insufficient_funds":
        sub_note = " Active subscription at risk." if payment.subscription_active else ""
        return Diagnosis(
            root_cause="customer_funding_issue",
            reasoning=(
                f"Payment of INR {payment.amount:,} failed due to insufficient funds. "
                f"A low-friction payment link is safer than repeated immediate retries.{sub_note}"
            ),
            recommended_action="send_recovery_link",
            recovery_channel="sms",
        )

    if payment.failure_type == "mandate_failure" and payment.subscription_active:
        return Diagnosis(
            root_cause="mandate_or_subscription_failure",
            reasoning=(
                f"Subscription mandate failed for INR {payment.amount:,}. "
                f"Customer has {payment.previous_successes} prior successful payments. "
                f"A sequenced retry may recover the mandate before escalation."
            ),
            recommended_action="delayed_retry",
            recovery_channel="auto_retry",
        )

    if risk.priority == "LOW":
        return Diagnosis(
            root_cause="low_recovery_likelihood",
            reasoning=(
                f"Recovery probability is only {risk.probability:.0%}. "
                f"The case has weak recovery signals and should not consume automatic retry budget."
            ),
            recommended_action="escalate",
            recovery_channel="none",
        )

    return Diagnosis(
        root_cause="issuer_or_mandate_decline",
        reasoning=(
            f"Issuer or mandate decline for INR {payment.amount:,}. "
            f"The failure may recover through a sequenced retry with strict limits. "
            f"Customer has {payment.previous_successes} prior successes."
        ),
        recommended_action="delayed_retry",
        recovery_channel="auto_retry",
    )


def plan_recovery(payment: PaymentEvent, diagnosis: Diagnosis) -> RecoveryPlan:
    if diagnosis.recommended_action == "delayed_retry":
        return RecoveryPlan(
            action="retry_payment",
            delay_minutes=30,
            max_retries=2,
            explanation="Retry once after bank rails settle; escalate if retry budget is exhausted.",
            recovery_channel=diagnosis.recovery_channel,
        )

    if diagnosis.recommended_action == "send_recovery_link":
        return RecoveryPlan(
            action="send_payment_link",
            delay_minutes=0,
            max_retries=1,
            explanation="Send a Razorpay payment link so the customer can use a fresh method.",
            recovery_channel=diagnosis.recovery_channel,
        )

    return RecoveryPlan(
        action="escalate",
        delay_minutes=0,
        max_retries=0,
        explanation="Stop automation and route the case to a human operator.",
        recovery_channel="none",
    )
