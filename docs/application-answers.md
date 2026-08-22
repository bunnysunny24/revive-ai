# Buildathon Application Answers (Track 03)

## Track
`03 — AI Revenue Recovery`

## Project Name
`ReviveAI`

## What It Solves
Failed payments, abandoned checkouts, and subscription drop-offs silently drain merchant revenues. Most payment gateways notify merchants of failure, but do not close the loop. ReviveAI closes the loop from automated failure detection and contextual root-cause diagnosis to deterministic policy gating, multi-channel recovery execution (automated retries, SMS/Email payment links), and measured revenue reporting across 10,000-payment batches.

## Short Description
ReviveAI is an autonomous, policy-bounded revenue recovery engine for merchants. It pairs a trainable lightweight ML risk model and explainable heuristic scorer with contextual AI diagnosis, 6-gate deterministic policy controls, simulated Razorpay test execution, multi-channel recovery tracking, and an immutable audit trail.

## What Broke, And How I Got Out
*Initial failure mode:* In early development, simulated payment gateway API timeouts (504 errors) caused automated recovery loops to immediately re-trigger retries, rapidly exhausting customer retry budgets and risking unintended multiple charges. Furthermore, static asset serving had potential path-traversal vulnerabilities.

*How I fixed it:*
1. **Separation of Policy from Execution**: Created a strict 6-gate deterministic policy engine where provider outages preserve the retry budget rather than consuming it, immediately routing the transaction to human review with an immutable audit event (`provider_failure_escalated`).
2. **Deterministic Stopping Rules**: Enforced a hard INR 10,000 amount cap, 30-minute cooldown windows, customer opt-out compliance, and idempotency checks to eliminate double-charges.
3. **Hardened HTTP & Thread Safety**: Enforced strict boundary checks (`is_relative_to`) in the static file server and added re-entrant thread locks (`threading.RLock`) in the core state repository.

## Why This Uses AI Meaningfully
ReviveAI uses the right tool for each layer without turning financial operations into an unconstrained LLM chatbot:
- **Risk Scoring**: Evaluates recovery likelihood using a pure-Python Logistic Regression classifier (`F1: 0.586` on held-out test data) benchmarked against an interpretable baseline (`F1: 0.561`).
- **Contextual Diagnosis**: Evaluates customer tier, historical success/failure counts, and failure taxonomy to generate dynamic, human-readable root-cause explanations and prescribe the optimal channel (Auto-retry, SMS, or Email).
- **Deterministic Policy Controls**: Rather than allowing generative models to directly issue refunds or retries, all money actions are gated by strict, explainable rules.

## Evidence Of Value
Evaluated on a 10,000-payment synthetic dataset (with 70/15/15 train/val/test split):
- **Recovered Revenue**: INR 7,026,643 across 2,272 successful recoveries
- **Batch Recovery Rate**: 89.8% on actionable interventions
- **Channel Breakdown**:
  - Automated Rail Retries: INR 5,214,053
  - SMS Payment Links: INR 1,390,487
  - Email Payment Links: INR 422,103
- **Safety Compliance**: 0.0% unauthorized actions, 0 policy violations, 0 retry-limit violations
- **Held-Out Test ML F1 Score**: 0.586 (Validation-selected threshold: 0.30)
- **Unit Test Coverage**: 15/15 passing tests

## Public GitHub Repository Checklist
- [x] Public repository: https://github.com/bunnysunny24/revive-ai
- [x] Live deployed demo: https://revive-ai-hlmx.onrender.com
- [x] Zero external dependencies (runs on any Python 3.10+ standard library)
- [x] Comprehensive README with quickstart and architecture diagrams
- [x] Full evaluation report and ML model artifact (`models/risk_model.json`)
- [x] Detailed failure mode analysis (`docs/failure-modes.md`)
- [x] Timed 5-minute pitch video script (`docs/pitch-script.md`)
- [x] All 15 unit tests passing

