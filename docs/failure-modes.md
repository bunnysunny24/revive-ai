# Failure Modes

The buildathon brief asks for one failure and how the system recovered. ReviveAI includes that path directly in the demo.

## Failure: Provider Timeout

Some simulated Razorpay test actions return:

```text
provider_status: api_error
message: Simulated Razorpay test API timeout.
```

## Bad Behavior Avoided

The system does not retry forever and does not mutate the payment into a recovered state.

## Recovery Behavior

When the provider action fails:

1. The action is recorded in the audit trail.
2. Retry budget is preserved.
3. The payment is escalated to human review.
4. No extra money action is attempted.
5. The dashboard shows the failed provider event and escalation.

## Why This Matters

Financial AI systems need bounded behavior more than clever phrasing. This failure path shows that ReviveAI treats provider uncertainty as a control problem, not a prompt problem.
