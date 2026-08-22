# Buildathon Application Answers

## Track

03 - AI Revenue Recovery

## Project Name

ReviveAI

## What It Solves

ReviveAI recovers revenue from failed payments, checkout abandonment, and subscription-style failures. It does not stop at detecting failed payments. It diagnoses likely root cause, recommends a recovery workflow, gates the action through deterministic policy, executes a Razorpay-compatible test-mode action, and reports recovered revenue across a batch.

## Short Description

ReviveAI is an autonomous revenue recovery system for merchants. It combines interpretable risk scoring, a trainable lightweight ML risk model, AI-style diagnosis, bounded recovery planning, deterministic policy checks, Razorpay test-mode execution, and complete audit trails.

## What Broke, And How I Got Out

The first version made the batch recovery workflow too aggressive. It processed every actionable case in one request and the demo path could take too long. More importantly, provider failures needed to be handled as a control-flow problem, not as "try again until it works."

I fixed this by adding a deterministic policy engine and a bounded batch runner. Every recovery action now checks retry budget, amount limit, customer opt-out, cooldown, and payment state. Simulated Razorpay provider errors are recorded in the audit trail, retry budget is preserved, and the case is escalated to human review instead of entering an automatic retry loop.

## Why This Uses AI Meaningfully

The system uses the right tool at each layer. Risk scoring ranks recoverable revenue, and the evaluation script trains a lightweight logistic model on synthetic labels to compare against the interpretable baseline. The diagnosis agent interprets payment context and recommends retry, payment link, or escalation. The policy engine, not the AI, controls financial execution. This keeps the workflow explainable, bounded, gated, and auditable.

## Evidence Of Value

The evaluation script runs on 10,000 synthetic failed-payment records, trains a model artifact, and reports precision, recall, F1, false-positive cost, recovered revenue, recovery rate, escalations, provider failures handled, and policy violations.

Latest seeded report:

- Payments analyzed: 10,000
- Predicted at risk: 7,601
- Interventions attempted: 2,529
- Recoveries: 2,272
- Recovered revenue: INR 7,026,643
- Recovery rate: 89.8%
- Policy violation rate: 0.0%
- Trainable model held-out F1: 0.586
- Heuristic baseline held-out F1: 0.561

## GitHub Repo Checklist

- Public repository
- README with quickstart
- Architecture document
- Evaluation report
- Failure-mode writeup
- Demo video link
- No real API keys committed
