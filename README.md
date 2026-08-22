# ReviveAI

AI-powered autonomous revenue recovery for failed payments.

ReviveAI detects revenue at risk, diagnoses why a payment is likely to be lost, selects a bounded recovery workflow, executes the approved action through a Razorpay-compatible test adapter, and measures recovered revenue across a synthetic batch.

## Track

Razorpay AI Buildathon - Track 03: AI Revenue Recovery

## Demo Metrics

The included synthetic evaluation processes 10,000 payment events and reports:

- Payments analyzed
- At-risk payments
- Interventions attempted
- Recovered revenue
- Recovery rate
- Human escalations
- Policy blocks
- Failed interventions
- Policy violations

Latest seeded run:

- `10,000` payments analyzed
- `7,601` predicted at-risk payments
- `2,529` interventions attempted
- `INR 7,026,643` recovered
- `89.8%` recovery rate
- `0` policy violations
- Trainable ML model held-out F1: `0.586`
- Heuristic baseline held-out F1: `0.561`

## Why This Is Not Just An LLM Wrapper

ReviveAI separates judgment from control:

- A trainable logistic risk model and interpretable baseline estimate recovery likelihood.
- Diagnosis agent explains failure causes and recommends an intervention.
- Policy engine gates every money action with retry, amount, consent, and cooldown limits.
- Razorpay adapter executes only approved test-mode workflows.
- Audit log records every decision, action, outcome, and stop condition.

## System Architecture

```text
Synthetic payment events
  -> heuristic + trainable risk scoring
  -> diagnosis agent
  -> recovery planner
  -> deterministic policy engine
  -> Razorpay test adapter
  -> outcome tracker
  -> audit + evaluation report
```

## Run Locally

```bash
python scripts/generate_dataset.py --records 10000
python scripts/evaluate.py
python -m unittest discover -s tests
python backend/server.py
```

Then open:

```text
http://localhost:8000
```

## Useful Endpoints

- `GET /api/summary` - aggregate evaluation and recovery metrics
- `GET /api/payments?limit=20` - recent payment cases
- `GET /api/payments/{payment_id}` - payment, diagnosis, plan, audit trail
- `POST /api/payments/{payment_id}/execute` - execute next bounded recovery action
- `POST /api/demo/reset` - rebuild the deterministic demo state
- `POST /api/demo/run-batch` - process a bounded recovery batch for the demo

## ML Artifact

Running `python scripts/evaluate.py` trains a pure-Python logistic regression model and saves:

```text
models/risk_model.json
```

The report compares:

- interpretable heuristic risk scoring
- trainable ML risk scoring
- business recovery metrics
- policy and safety metrics

Latest model result:

- validation-selected threshold: `0.30`
- test precision: `0.459`
- test recall: `0.810`
- test F1: `0.586`

## Razorpay Test Mode

The app ships with a local Razorpay-compatible simulator so reviewers can run it without credentials. To connect real Razorpay test-mode calls, implement the adapter in `backend/app/razorpay_adapter.py` and set:

```text
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_MODE=test
```

The policy engine remains mandatory even when real test APIs are enabled.

## Application Assets

- Architecture: `docs/architecture.md`
- Evaluation: `docs/evaluation.md`
- Failure modes: `docs/failure-modes.md`
- Pitch script: `docs/pitch-script.md`
- Application answers: `docs/application-answers.md`

## Demo Path

1. Open the dashboard.
2. Click `Run Batch` to show recovered revenue across hundreds of cases.
3. Open `DEMO_SUCCESS` or the first approved case and execute recovery.
4. Open `DEMO_BLOCKED` to show a high-value policy block.
5. Open `DEMO_FAIL7` and execute it to show provider failure handling and escalation.

## Buildathon Form Summary

Project name: ReviveAI

What it solves: Failed payments, abandoned checkouts, and subscription failures leak revenue because merchants often detect the failure but do not close the loop. ReviveAI closes the loop from detection to diagnosis to bounded recovery action to measured recovered revenue.

What broke: The first recovery workflow retried simulated API failures too aggressively. I fixed it by moving retry limits into a deterministic policy engine, preserving retry budget on provider errors, creating audit records for every failed action, and escalating instead of looping.
