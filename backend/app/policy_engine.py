from .models import PaymentEvent, PolicyDecision, RecoveryPlan


MAX_AUTOMATIC_AMOUNT = 10000
MIN_RETRY_COOLDOWN_MINUTES = 30


def evaluate_policy(payment: PaymentEvent, plan: RecoveryPlan) -> PolicyDecision:
    if payment.customer_opted_out:
        return PolicyDecision(False, "Customer opted out of recovery contact.")

    if plan.action == "escalate":
        return PolicyDecision(False, "Human escalation requested by diagnosis.")

    if payment.amount > MAX_AUTOMATIC_AMOUNT:
        return PolicyDecision(False, "Amount exceeds automatic recovery limit.")

    if payment.attempts >= plan.max_retries:
        return PolicyDecision(False, "Retry budget exhausted.")

    if plan.action == "retry_payment" and payment.last_attempt_minutes < MIN_RETRY_COOLDOWN_MINUTES:
        return PolicyDecision(False, "Retry cooldown window has not elapsed.")

    if payment.status == "captured" or payment.recovered:
        return PolicyDecision(False, "Payment is already recovered.")

    return PolicyDecision(True, "Approved by amount, consent, retry, and cooldown policy.")
